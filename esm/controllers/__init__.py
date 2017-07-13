import connexion


def _version_ok():
    # TODO create a decorator out of this

    version_requested = connexion.request.headers.get('X-Broker-Api-Version', None)

    if not version_requested:
        return False, 'No X-Broker-Api-Version header supplied in the request. This endpoint supports 2.12.', 400
    elif version_requested != '2.12':
        return False, 'The X-Broker-Api-Version header is not supported. This endpoint supports 2.12.', 400
    else:
        return True, 'Requested API version is acceptable.', 201
