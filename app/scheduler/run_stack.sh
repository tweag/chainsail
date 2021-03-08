docker-compose --file example/docker-compose.yaml up &

sleep 5

export LD_LIBRARY_PATH=$(nix eval --raw nixpkgs.stdenv.cc.cc.lib)/lib:$LD_LIBRARY_PATH
export PYTHONPATH="PYTHONPATH:$PWD"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/1"
export SQLALCHEMY_DATABASE_URI="postgresql://postgres:resaas-dev@localhost:5432/postgres"
export RESAAS_SCHEDULER_CONFIG="$PWD/example/scheduler.yaml"

celery --app "resaas.scheduler.tasks.celery" worker --task-events --pool gevent --concurrency=1 &
python -m 'resaas.scheduler.app' &

sleep 5

curl --request POST --header "Content-Type: application/json" --data '{"probability_definition": "gs://foo/bar", "initial_number_of_replicas": "2"}' http://127.0.0.1:5000/job
curl --request POST http://127.0.0.1:5000/internal/job/1/add_iteration/optimization_run1
curl --request POST http://127.0.0.1:5000/internal/job/1/add_iteration/optimization_run2
curl --request POST http://127.0.0.1:5000/internal/job/1/add_iteration/production_run
