package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"voiceservice/pkg/voiceservice"
)

func main() {
	err := run()
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

var (
	parallelism = flag.Int("parallelism", 3, "Number of concurrent jobs")
	hwAccel     = flag.Bool("hw-accel", true, "Enable hardware acceleration")
	queueSize   = flag.Int("queue-size", 10, "Size of the job queue")
	target      = flag.String("target", "localhost:50053", "gocast server to push subtitles to")
	authToken   = flag.String("auth-token", "", "if configured, the token is required as grpc metadata field 'auth' for incoming requests "+
		"and attached to gRPC metadata for outgoing requests.")
)

func run() error {
	flag.Parse()
	log.Printf("Starting voice service with parallelism=%d, hw-accel=%v, queue-size=%d\n", *parallelism, *hwAccel, *queueSize)
	ctx := context.Background()
	ctx, cancel := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)
	defer cancel()
	return voiceservice.New(*parallelism, *queueSize, *hwAccel, *target, *authToken).Run(ctx)
}
