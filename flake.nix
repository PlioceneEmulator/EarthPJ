{
  inputs = {
    nixpkgs = {
      url = "github:nixos/nixpkgs/nixos-unstable";
    };
    flake-utils = {
      url = "github:numtide/flake-utils";
    };
  };
  outputs = {
    nixpkgs,
    flake-utils,
    ...
  } @ inputs:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {
          inherit system;
        };

        lib = import flake-utils.lib {inherit pkgs;};
        # inherit (pkgs) stdenv lib;
        inherit (pkgs) stdenv;

        pythonPackages = lib.fix' (self:
          with self;
            pkgs.python3Packages
            // {
              cartopy = buildPythonPackage rec {
                pname = "cartopy";
                version = "0.21.0";

                src = fetchPypi {
                  inherit pname version;
                  sha256 = "sha256-zh06KKEy6UyJrDN2mlD4H2VjSrK9QFVjF+Fb1srRzkI=";
                };

                postPatch = ''
                  # https://github.com/SciTools/cartopy/issues/1880
                  substituteInPlace lib/cartopy/tests/test_crs.py \
                    --replace "test_osgb(" "dont_test_osgb(" \
                    --replace "test_epsg(" "dont_test_epsg("
                '';

                nativeBuildInputs = [
                  cython
                  geos # for geos-config
                  proj
                  setuptools-scm
                ];

                buildInputs = [
                  geos
                  proj
                ];

                propagatedBuildInputs = [
                  # required
                  six
                  pyshp
                  shapely
                  numpy

                  # optional
                  gdal
                  pillow
                  matplotlib
                  pyepsg
                  pykdtree
                  scipy
                  fiona
                  owslib
                ];

                checkInputs = [pytestCheckHook filelock mock pep8 flufl_lock];
                pytestFlagsArray = [
                  "--pyargs"
                  "cartopy"
                  "-m"
                  "'not network and not natural_earth'"
                ];

                disabledTests = [
                  "test_nightshade_image"
                  "background_img"
                  "test_gridliner_labels_bbox_style"
                ];
              };
            });

        metpy = with pkgs.python310Packages;
          buildPythonPackage rec {
            pname = "MetPy";
            version = "1.4.1";
            src = fetchPypi {
              inherit pname version;
              sha256 = "sha256-oT3S2jYOv9hWJw5BdG5P1Uutyp3NvYASKegDgs4x27k=";
            };
            buildInputs = with inputs.nixpkgs; [
              matplotlib
              numpy
              pandas
              pint
              pooch
              pyproj
              scipy
              traitlets
              xarray
              importlib-resources
              importlib-metadata
            ];
            doCheck = false;
          };

        cmaps = with pkgs.python310Packages;
          buildPythonPackage rec {
            pname = "cmaps";
            version = "1.0.5";
            src = fetchPypi {
              inherit pname version;
              sha256 = "sha256-jucIv2xAJNzQYNZYqgy7p0CsBHLlY4UStHZN6h6SjEY=";
            };
            buildInputs = with inputs.nixpkgs; [
              numpy
              matplotlib
              traitlets
            ];
            doCheck = false;
          };

        geocat-viz = pkgs.python3Packages.buildPythonPackage rec {
          pname = "geocat.viz";
          # version = "2022.7.0";
          version = "2023.3.0.post0";
          src = pkgs.python3Packages.fetchPypi {
            inherit pname version;
            sha256 = "sha256-gs6Hz71GVwwxAEkMSBmLHHm5XBzwcx8x57yah2492Ig=";
          };
          propagatedBuildInputs = with pkgs.python3Packages; [cmaps metpy cartopy xarray scikit-learn pint traitlets pooch];
        };
      in rec {
        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
            (python3.withPackages (ps:
              with ps; [
                certifi
                charset-normalizer
                click
                wheel
                cartopy
                metpy
                cmaps
                geocat-viz
                contourpy
                cycler
                flask
                fonttools
                geos
                idna
                itsdangerous
                jinja2
                joblib
                kiwisolver
                lxml
                markupsafe
                matplotlib
                numpy
                packaging
                pandas
                pillow
                pint
                platformdirs
                pooch
                pyparsing
                pyproj
                pyshp
                python-dateutil
                pytz
                requests
                scikit-learn
                scipy
                shapely
                six
                threadpoolctl
                traitlets
                urllib3
                werkzeug
                xarray
              ]))
          ];
          shellHook = "python ./webapp.py";
        };
      }
    );
}
