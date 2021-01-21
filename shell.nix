{ pkgs ? import ./nix {} }:
pkgs.mkShell {
  buildInputs = with pkgs; [
    python38
    python38Packages.poetry
    niv.niv
    yarn
    docker-compose
  ];
}
