# scheduler

## Running the dev server

As of right now, you need to enter the nix shell then run 
the app module directly. As of today this uses a local sqlite database
in /tmp.

```shell
$ nix-shell ../shell.nix
$ poetry install
$ poetry shell
$ cd ..
$ PYTHONPATH="$PYTHONPATH:$PWD/scheduler" python scheduler/resaas/scheduler/app.py
```

then, for example:

```shell
curl --request POST \
     --header "Content-Type: application/json" \
     --data '{"probability_definition": "gs://foo/bar"}' \
     http://127.0.0.1:5000/job
```

## Development

To activate dev environment: 

```shell
$ nix-shell ../shell.nix
$ poetry install
```
