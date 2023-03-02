{ pkgs ? import ./nix { } }:
pkgs.mkShell {
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
    poetry # version 1.1.10 (required) while pythonPackages38.poetry is lower
    python38Packages.tkinter
    terraform
    yarn
    zlib
  ];

  # Setting the LD_LIBRARY_PATH environment variable.
  # Can also make use of the `.overrideAttrs` method to prevent from overwriting it.
  # See PR #310 for details: https://github.com/tweag/chainsail/pull/310.
  LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.file}/lib:${pkgs.zlib}/lib";
}
