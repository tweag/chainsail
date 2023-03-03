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
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            docker-compose
            file
            gnumake
            kubectl
            kubernetes-helm
            minikube
            ncurses
            nodejs
            openmpi
            poetry
            python38Packages.tkinter
            terraform
            yarn
            zlib
          ];

          # Setting the LD_LIBRARY_PATH environment variable.
          # Can also make use of the `.overrideAttrs` method to prevent from overwriting it.
          # See PR #310 for details: https://github.com/tweag/chainsail/pull/310.
          LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.file}/lib:${pkgs.zlib}/lib";
        };
        packages = {
          controller = poetry2nixPkg.mkPoetryApplication {
            projectDir = ./app/controller;
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
                // addNativeBuildInputs "mpi4py" [ final.cython ]
                // addNativeBuildInputs "rexfw" [ final.poetry-core ]
            );
          };
          default = self.packages.${system}.controller;
        };
      }
    );
}
