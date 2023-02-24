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
  overrides = poetry2nix.overrides.withDefaults (
    final: prev: {
      mpi4py = prev.mpi4py.overrideAttrs (
        old: {
          buildInputs =
            (old.buildInputs or [ ]) ++ [ pkgs.python3Packages.cython ];
        }
      );
      rexfw = prev.rexfw.overrideAttrs (
        old: {
          buildInputs =
            (old.buildInputs or [ ]) ++ [ pkgs.poetry ];
        }
      );
    }
  );
}
