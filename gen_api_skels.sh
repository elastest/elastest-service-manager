#!/usr/bin/env bash

# assumes installation of swagger code gen
SWAGGER_CODE_GEN="/usr/local/bin/swagger-codegen"

# generate the skeletons for the server process
# mapping object to # is the only way to remove this generation AFAIK
# -DsupportPython2=true <- only if required, by default no.
 $SWAGGER_CODE_GEN generate -i  ./api.yaml -l python-flask -o ./src/ -DpackageName=esm --import-mappings object=#

# generate gRPC stubs
# python -m grpc_tools.protoc --python_out=. --grpc_python_out=. --proto_path=. ./backend_osba_adapter.proto