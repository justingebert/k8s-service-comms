REGISTRY ?= local
RUN_ID ?= $(shell date +%Y%m%d_%H%M%S)_same-node_http8080_emptyDirDisk

.PHONY: build destroy apply teardown-apply deploy-net deploy-file run-sender wait-sender collect plot all

build:
	eval $$(minikube docker-env) && \
	docker build -t net-receiver:local -f docker/net-receiver.Dockerfile . && \
	docker build -t net-sender:local -f docker/net-sender.Dockerfile . && \
	docker build -t file-reader:local -f docker/file-reader.Dockerfile . && \
	docker build -t file-writer:local -f docker/file-writer.Dockerfile .


destroy:
	kubectl delete -R -f k8s/ --ignore-not-found

apply:
	kubectl apply -R -f k8s/

teardown-apply:
	kubectl delete -R -f k8s/ --ignore-not-found
	kubectl wait --for=delete pod --all --timeout=300s || true
	kubectl apply -R -f k8s/

deploy-net:
	kubectl apply -f k8s/net/reciever.yaml
	kubectl apply -f k8s/net/net-svc.yaml
	kubectl rollout status deploy/net-receiver --timeout=60s

deploy-file:
	kubectl delete pod/file-bench --ignore-not-found
	kubectl apply -f k8s/file/file-bench.yaml

run-sender:
	kubectl delete job/net-sender --ignore-not-found
	kubectl apply -f k8s/net/sender.yaml

wait-sender:
	kubectl wait --for=condition=complete job/net-sender --timeout=600s

collect:
	mkdir -p results/runs/$(RUN_ID)
	kubectl logs job/net-sender > results/runs/$(RUN_ID)/net-raw.csv
	kubectl logs pod/file-bench -c writer > results/runs/$(RUN_ID)/file-raw.csv

plot:
	python3 vis/plot_bench.py

all: build deploy-net deploy-file run-sender wait-sender collect plot
