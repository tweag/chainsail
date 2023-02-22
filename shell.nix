{ pkgs ? import ./nix { } }:
pkgs.mkShell {
  buildInputs = with pkgs; [
    poetry # version 1.1.10 (required) while pythonPackages38.poetry is lower
    yarn
    nodejs
    docker-compose
    openmpi
    # python38Packages.tkinter
    ncurses
    file
    gnumake
    terraform
    kubernetes-helm
    minikube
    kubectl
  ];
  # Setting the LD_LIBRARY_PATH environment variable.
  # Can also make use of the `.overrideAttrs` medthod to prevent from overwriting it (See PR #310 for details)
  LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.file}/lib";
}
