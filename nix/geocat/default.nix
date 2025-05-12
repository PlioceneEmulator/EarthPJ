{pkgs ? import <nixpkgs> {}}: let
  geocatViz = pkgs.python3Packages.buildPythonPackage {
    pname = "geocat-viz";
    version = "0.6.0";
    src = pkgs.fetchgit {
      url = "https://github.com/NCAR/geocat-viz.git";
      sha256 = "sha256-p7GYHkkiVbTVhJY/+uNnfQbGe71CvYk9DBaogUwgPnU=";
    };
    propagatedBuildInputs = [
      pkgs.python3
      pkgs.python39Packages.wheel
    ];
    buildInputs = [
      # pkgs.cartopy
      pkgs.python39Packages.setuptools
      pkgs.python39Packages.xarray
      pkgs.python39Packages.matplotlib
      pkgs.python310Packages.cartopy
    ];
  };
in
  geocatViz
