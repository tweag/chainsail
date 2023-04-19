{
  description = "Chainsail";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "nixpkgs/release-22.11";
    yarn-nixpkgs.url = "nixpkgs/21.11";
    poetry2nix = {
      url = "github:steshaw/poetry2nix/git-branch-dependency";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        flake-utils.follows = "flake-utils";
      };
    };
  };

  outputs = { self, flake-utils, nixpkgs, yarn-nixpkgs, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        nodePkgs = yarn-nixpkgs.legacyPackages.${system};
        poetry2nixPkg = poetry2nix.legacyPackages.${system};
        ourNode = pkgs.nodejs-14_x;
        ourYarn = nodePkgs.yarn.override(_: {
          nodejs = ourNode;
        });
        controllerOverrides = final: prev:
          let
            addNativeBuildInputs = drvName: inputs: {
              "${drvName}" = prev.${drvName}.overridePythonAttrs (
                old: {
                  nativeBuildInputs =
                    (old.nativeBuildInputs or [ ]) ++ inputs;
                }
              );
            };
          in
          { }
          // addNativeBuildInputs "mpi4py" [ final.cython ]
          // addNativeBuildInputs "rexfw" [ final.poetry-core ]
          // addNativeBuildInputs "chainsail-helpers" [ final.poetry-core ];

        controllerOpts = {
          projectDir = ./app/controller;
          overrides = poetry2nixPkg.overrides.withDefaults(controllerOverrides);
          preferWheels = true;
        };
        controller = poetry2nixPkg.mkPoetryApplication controllerOpts;
        controllerEnv = poetry2nixPkg.mkPoetryEnv controllerOpts;
        controller-image = pkgs.dockerTools.streamLayeredImage {
          name = "chainsail-mpi-node-k8s";
          contents = [ controller ];
          config.Cmd = [ "chainsail-controller" ];
        };

        basePackages = [
          pkgs.docker-compose
          pkgs.file
          pkgs.gnumake
          pkgs.kubectl
          pkgs.kubernetes-helm
          pkgs.minikube
          pkgs.ncurses
          ourNode
          pkgs.openmpi
          pkgs.poetry
          pkgs.terraform
          ourYarn
        ];

        mkDevShell = {extraPkgs ? []}: pkgs.mkShell {
          packages = extraPkgs ++ basePackages;
          shellHook = ''
            private_env_sh=.config/env.private.sh
            if [[ -r $private_env_sh ]]; then
              echo loading $private_env_sh
              source $private_env_sh
            fi
            unset private_env_sh
          '';
        };
        controllerDevShell = mkDevShell {
          extraPkgs = [
            controllerEnv
            controller
          ];
        };
      in
      {
        devShells = {
          controller = controllerDevShell;
          default = mkDevShell {};
        };
        packages = {
          inherit controller;
          inherit controller-image;
          scheduler = poetry2nixPkg.mkPoetryApplication {
            projectDir = ./app/scheduler;
            overrides = poetry2nixPkg.overrides.withDefaults (
              final: prev:
                let
                  addNativeBuildInputs = drvName: inputs: {
                    "${drvName}" = prev.${drvName}.overridePythonAttrs (
                      old: {
                        nativeBuildInputs =
                          (old.nativeBuildInputs or [ ]) ++ inputs;
                      }
                    );
                  };
                in
                { }
                // addNativeBuildInputs "uwsgi" [ final.setuptools ]
                // addNativeBuildInputs "firebase-admin" [ final.setuptools ]
            );
          };
          default = self.packages.${system}.controller;
        };
      }
    );
}
