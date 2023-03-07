{
  description = "Chainsail";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "nixpkgs/release-22.11";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, flake-utils, nixpkgs, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        poetry2nixPkg = poetry2nix.legacyPackages.${system};

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

        basePackages = [
          pkgs.docker-compose
          pkgs.file
          pkgs.gnumake
          pkgs.kubectl
          pkgs.kubernetes-helm
          pkgs.minikube
          pkgs.ncurses
          pkgs.nodejs
          pkgs.openmpi
          pkgs.poetry
          pkgs.python38Packages.tkinter
          pkgs.terraform
          pkgs.yarn
        ];

        pythonDevShell = ps: pkgs.mkShell {
          packages = ps ++ basePackages;
        };
        controllerDevShell = pythonDevShell [
          controllerEnv
          controller
        ];
      in
      {
        devShells = {
          controller = controllerDevShell;
          default = pkgs.mkShell { packages = basePackages; };
        };
        packages = {
          inherit controller;
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
