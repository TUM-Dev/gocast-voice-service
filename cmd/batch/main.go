package main

import (
	"context"
	"flag"
	"fmt"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"

	"voiceservice/gen/pb"
)

func main() {
	courseid := flag.Int("course", -1, "id of the course to create subtitles for.")
	lang := flag.String("lang", "en", "language to use, en or de.")
	admintoken := flag.String("admintoken", "", "admintoken to replace jwt for stream auth")
	dsn := flag.String("dsn", "", "dsn to connect to")
	srv := flag.String("srv", "localhost:50053", "subtitle server")

	flag.Parse()
	if *courseid == -1 || (*lang != "en" && *lang != "de") || *admintoken == "" || *dsn == "" {
		flag.Usage()
		return
	}

	db, err := gorm.Open(mysql.Open(*dsn), &gorm.Config{
		PrepareStmt: true,
	})
	if err != nil {
		fmt.Println(err.Error())
		return
	}
	var res []struct {
		ID          uint
		PlaylistURL string
	}
	err = db.Debug().Raw(`SELECT s.id, playlist_url
FROM streams s
         LEFT JOIN subtitles st ON st.stream_id = s.id
WHERE s.deleted_at IS NULL
  AND s.recording
  AND s.course_id = ?
  AND st.id IS NULL`, *courseid).Scan(&res).Error
	if err != nil {
		fmt.Println(err.Error())
	}
	c, err := dial(*srv)
	if err != nil {
		fmt.Println(err.Error())
		return
	}

	for _, r := range res {
		fmt.Println(r.PlaylistURL)
		_, err = c.Generate(context.Background(), &pb.GenerateRequest{
			StreamId: int32(r.ID),
			Source:   r.PlaylistURL + "?jwt=" + *admintoken,
			Language: *lang,
		})
		if err != nil {
			fmt.Println(err.Error())
		}
	}
}

func dial(srv string) (pb.SubtitleGeneratorClient, error) {
	conn, err := grpc.NewClient(srv, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, err
	}
	return pb.NewSubtitleGeneratorClient(conn), nil
}
