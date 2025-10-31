docker build -t net-receiver:local -f net-receiver.Dockerfile ../
docker build -t net-sender:local -f net-sender.Dockerfile ../
docker build -t file-reader:local -f file-reader.Dockerfile ../
docker build -t file-writer:local -f file-writer.Dockerfile ../
