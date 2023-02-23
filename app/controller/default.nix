{ pkgs ? import ../../nix { }
}:
let
  p2nSrc = fetchTarball
    https://github.com/steshaw/poetry2nix/tarball/git-branch-dependency;
  poetry2nix = import p2nSrc {
    inherit pkgs;
    inherit (pkgs) poetry;
  };
in
poetry2nix.mkPoetryApplication {
  projectDir = ./.;
}
