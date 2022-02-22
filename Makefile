
#################################
# Docker targets
#################################
.PHONY: images
images:
	@echo "Building docker images..."
	docker build -t "${HUB_NAMESPACE}/chainsail-celery-worker:latest" -f ./docker/celery/Dockerfile .
	docker build -t "${HUB_NAMESPACE}/chainsail-scheduler:latest" -f ./docker/scheduler/Dockerfile .
	docker build -t "${HUB_NAMESPACE}/chainsail-nginx:latest" -f ./docker/nginx/Dockerfile .
	docker build -t "${HUB_NAMESPACE}/chainsail-client:latest" -f app/client/Dockerfile app/client
	docker build -t "${HUB_NAMESPACE}/chainsail-user-code:latest" -f docker/user-code/Dockerfile .
	docker build -t "${HUB_NAMESPACE}/httpstan-server:latest" -f docker/httpstan-server/Dockerfile .
	docker build -t "${HUB_NAMESPACE}/chainsail-mpi-node-k8s:latest" -f docker/node/Dockerfile .
	docker build -t "${HUB_NAMESPACE}/chainsail-mcmc-stats-server:latest" -f docker/mcmc-stats-server/Dockerfile .
	@echo "Done."

.PHONY: push-images
push-images: images
	@echo "Pushing docker images..."
	docker push "${HUB_NAMESPACE}/chainsail-celery-worker:latest"
	docker push "${HUB_NAMESPACE}/chainsail-scheduler:latest"
	docker push "${HUB_NAMESPACE}/chainsail-nginx:latest"
	docker push "${HUB_NAMESPACE}/chainsail-client:latest"
	docker push "${HUB_NAMESPACE}/chainsail-user-code:latest"
	docker push "${HUB_NAMESPACE}/httpstan-server:latest"
	docker push "${HUB_NAMESPACE}/chainsail-mpi-node-k8s:latest"
	docker push "${HUB_NAMESPACE}/chainsail-mcmc-stats-server:latest"
	@echo "Done."
