package voiceservice

import (
	"context"
	"crypto/subtle"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"voiceservice/gen/pb"

	containerapi "github.com/docker/docker/api/types/container"
	"github.com/docker/go-sdk/container"
	"github.com/google/uuid"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/emptypb"
)

type App struct {
	pb.UnimplementedSubtitleGeneratorServer

	hw     bool // true if hw acceleration is enabled
	jobs   chan *pb.GenerateRequest
	target string // server to which to push the subtitles

	subtitleReceiverClient pb.SubtitleReceiverClient
	parallelism            int
	authToken              string
}

func New(parallelism, queueSize int, hwacell bool, target string, authToken string) *App {
	return &App{
		hw:          hwacell,
		jobs:        make(chan *pb.GenerateRequest, queueSize), // buffer up to this many requests
		target:      target,
		parallelism: parallelism,
		authToken:   authToken,
	}
}

func (a *App) Run(ctx context.Context) error {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		return fmt.Errorf("failed to listen: %w", err)
	}

	s := grpc.NewServer(grpc.UnaryInterceptor(a.authInterceptor))
	pb.RegisterSubtitleGeneratorServer(s, a)

	defer close(a.jobs)

	errCh := make(chan error, 1)
	defer close(errCh)
	go func() {
		log.Printf("server listening at %v", lis.Addr())
		if err := s.Serve(lis); err != nil {
			errCh <- fmt.Errorf("failed to serve: %w", err)
		}
	}()

	for i := range a.parallelism {
		go func() {
			a.work(ctx, i)
		}()
	}

	select {
	case err := <-errCh:
		return err
	case <-ctx.Done():
		log.Println("shutting down server...")
		s.GracefulStop()
		return nil
	}
}

func (a *App) Generate(_ context.Context, req *pb.GenerateRequest) (*emptypb.Empty, error) {
	log.Printf("Received Generate request for stream %d with language %s", req.StreamId, req.Language)

	switch req.GetLanguage() {
	case "en", "EN", "English", "english":
		req.Language = "en"
	case "de", "DE", "Deutsch", "deutsch", "German", "german":
		req.Language = "de"
	default:
		return nil, status.Errorf(codes.InvalidArgument, "unsupported language %q", req.GetLanguage())
	}

	select {
	case a.jobs <- req:
	default:
		return nil, status.Errorf(codes.ResourceExhausted, "job queue is full")
	}

	return &emptypb.Empty{}, nil
}

func (a *App) work(ctx context.Context, i int) {
	log.Printf("Starting worker #%d", i)
	for {
		select {
		case req, ok := <-a.jobs:
			if !ok {
				return
			}
			log.Printf("handling request %s on worker %d", req, i)
			err := a.handle(ctx, req)
			if err != nil {
				log.Printf("failed to handle request: %v", err)
			}
		}
	}
}

func (a *App) handle(ctx context.Context, req *pb.GenerateRequest) error {
	image := "ghcr.io/jim60105/whisperx:large-v3-" + req.GetLanguage()
	fID := uuid.New().String()
	tempDir := "/tmp/whisper"
	_ = os.MkdirAll(tempDir, 0o777)

	tmpFile := filepath.Join(tempDir, fID+".m4a")
	defer func() {
		err := os.Remove(tmpFile)
		if err != nil {
			log.Println("could not remove temp file:", err)
		}
	}()

	cmd := exec.CommandContext(ctx, "ffmpeg", strings.Split("-loglevel warning -nostats -i "+req.GetSource()+" -c:a aac -vn "+tmpFile, " ")...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		return status.Error(codes.Internal, err.Error())
	}
	log.Printf("Audio converted and saved to %s", tmpFile)

	opts := []container.ContainerCustomizer{
		container.WithImage(image),
		container.WithAdditionalHostConfigModifier(func(hostConfig *containerapi.HostConfig) {
			hostConfig.Binds = append(hostConfig.Binds, fmt.Sprintf("%s:/app", tempDir))
		}),
		container.WithCmd("--", "--language", req.GetLanguage(), "--output_format", "vtt", filepath.Base(tmpFile)),
	}
	if a.hw {
		opts = append(opts, container.WithAdditionalHostConfigModifier(func(hostConfig *containerapi.HostConfig) {
			hostConfig.DeviceRequests = []containerapi.DeviceRequest{
				{
					Count:        -1,
					Capabilities: [][]string{{"gpu"}},
				},
			}
		}))
	}
	ctr, err := container.Run(
		ctx,
		opts...,
	)
	if err != nil {
		return status.Error(codes.Internal, err.Error())
	}
	log.Println("Container running, id: ", ctr.ID())

	defer func() {
		_ = ctr.Stop(ctx) // ignore error if already stopped. All good.
	}()

	for {
		if i, err := ctr.Inspect(ctx); err != nil || !i.State.Running {
			break
		}
		select {
		case <-ctx.Done():
		case <-time.After(time.Second):
		}
	}
	log.Println("Container finished")
	f, err := os.Open(filepath.Join(tempDir, fID+".vtt"))
	if err != nil {
		return status.Error(codes.Internal, err.Error())
	}
	subtitles, _ := io.ReadAll(f)
	log.Printf("Generated subtitles:\n%s", string(subtitles))
	err = a.dial()
	if err != nil {
		return err
	}
	outCtx := ctx
	if a.authToken != "" {
		outCtx = metadata.AppendToOutgoingContext(ctx, "auth", a.authToken)
	}
	_, err = a.subtitleReceiverClient.Receive(outCtx, &pb.ReceiveRequest{
		StreamId:  req.StreamId,
		Subtitles: string(subtitles),
		Language:  req.Language,
	})
	if err != nil {
		log.Println(err)
	}
	return nil
}

func (a *App) dial() error {
	conn, err := grpc.NewClient(a.target, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return err
	}
	a.subtitleReceiverClient = pb.NewSubtitleReceiverClient(conn)
	return nil
}

func (a *App) authInterceptor(ctx context.Context, req interface{}, _ *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
	if a.authToken == "" {
		return handler(ctx, req)
	}

	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return nil, status.Errorf(codes.Unauthenticated, "metadata is not provided")
	}

	values := md.Get("auth")
	if len(values) == 0 {
		return nil, status.Errorf(codes.Unauthenticated, "auth token is not provided")
	}

	if subtle.ConstantTimeCompare([]byte(values[0]), []byte(a.authToken)) != 1 {
		return nil, status.Errorf(codes.Unauthenticated, "invalid auth token")
	}

	return handler(ctx, req)
}
