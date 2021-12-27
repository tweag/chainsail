images:
	docker build -t "chainsail-celery-worker:latest" -f ./docker/celery/Dockerfile .
	docker build -t "chainsail-scheduler:latest" -f ./docker/scheduler/Dockerfile .
	docker build -t "chainsail-nginx:latest" -f ./docker/nginx/Dockerfile .
	docker build -t "chainsail-client:latest" -f app/client/Dockerfile app/client
	docker build -t chainsail-user-code:latest -f docker/user-code/Dockerfile .
	docker build -t httpstan-server:latest -f docker/httpstan-server/Dockerfile .
	docker build -t chainsail-mpi-node-k8s:latest -f docker/node/Dockerfile .