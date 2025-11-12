REGISTRY ?= local
RUN_ID ?= $(shell date +%y%m%d_%H%M)_same-node_http8080_emptyDirDisk

.PHONY: build destroy apply apply-config teardown-apply deploy-net deploy-file-disk deploy-file-memory deploy-file run-sender wait-sender wait-file-disk wait-file-memory collect plot all status debug

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

apply-config:
	kubectl apply -f k8s/bench-env.yaml

teardown-apply:
	kubectl delete -R -f k8s/ --ignore-not-found
	kubectl wait --for=delete pod --all --timeout=300s || true
	kubectl apply -R -f k8s/

deploy-net:
	kubectl apply -f k8s/net/receiver.yaml
	kubectl apply -f k8s/net/net-svc.yaml
	kubectl rollout status deploy/net-receiver --timeout=60s

deploy-file-disk:
	kubectl delete pod/file-bench-disk --ignore-not-found
	kubectl apply -f k8s/file/file-bench-disk.yaml

deploy-file-memory:
	kubectl delete pod/file-bench-memory --ignore-not-found
	kubectl apply -f k8s/file/file-bench-memory.yaml

deploy-file: deploy-file-disk deploy-file-memory

run-sender:
	kubectl delete job/net-sender --ignore-not-found
	kubectl apply -f k8s/net/sender.yaml

wait-sender:
	kubectl wait --for=condition=complete job/net-sender --timeout=600s

wait-file-disk:
	@while ! kubectl logs pod/file-bench-disk -c writer 2>/dev/null | tail -1 | grep -q "file-disk"; do sleep 2; done

wait-file-memory:
	@while ! kubectl logs pod/file-bench-memory -c writer 2>/dev/null | tail -1 | grep -q "file-memory"; do sleep 2; done

collect:
	mkdir -p results/runs/$(RUN_ID)
	kubectl logs job/net-sender > results/runs/$(RUN_ID)/net-raw.csv
	kubectl logs pod/file-bench-disk -c writer > results/runs/$(RUN_ID)/file-disk-raw.csv
	kubectl logs pod/file-bench-memory -c writer > results/runs/$(RUN_ID)/file-memory-raw.csv

plot:
	./.venv/bin/python3 vis/plot_bench.py

all: build apply-config deploy-net deploy-file run-sender wait-sender wait-file-disk wait-file-memory collect plot
