# coding: utf-8

from __future__ import absolute_import
from .base_model_ import Model
from datetime import date, datetime
from typing import List, Dict
from ..util import deserialize_model


class Manifest(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    def __init__(self, id: str=None, plan_id: str=None, service_id: str=None, manifest_type: str=None, manifest_content: str=None, endpoints: object=None, config: object=None):

        """Manifest - a model defined in Swagger

        :param id: The id of this Manifest.  # noqa: E501
        :type id: str
        :param plan_id: The plan_id of this Manifest.  # noqa: E501
        :type plan_id: str
        :param service_id: The service_id of this Manifest.  # noqa: E501
        :type service_id: str
        :param manifest_type: The manifest_type of this Manifest.  # noqa: E501
        :type manifest_type: str
        :param manifest_content: The manifest_content of this Manifest.  # noqa: E501
        :type manifest_content: str
        :param endpoints: The endpoints of this Manifest.  # noqa: E501
        :type endpoints: object
        :param config: The config of this Manifest.  # noqa: E501
        :type config: object
        """
        self.swagger_types = {
            'id': str,
            'plan_id': str,
            'service_id': str,
            'manifest_type': str,
            'manifest_content': str,
            'endpoints': object,
            'config': object
        }

        self.attribute_map = {
            'id': 'id',
            'plan_id': 'plan_id',
            'service_id': 'service_id',
            'manifest_type': 'manifest_type',
            'manifest_content': 'manifest_content',
            'endpoints': 'endpoints',
            'config': 'config'
        }

        self._id = id
        self._plan_id = plan_id
        self._service_id = service_id
        self._manifest_type = manifest_type
        self._manifest_content = manifest_content
        self._endpoints = endpoints
        self._config = config

    @classmethod
    def from_dict(cls, dikt) -> 'Manifest':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Manifest of this Manifest.  # noqa: E501
        :rtype: Manifest
        """
        return deserialize_model(dikt, cls)

    @property
    def id(self) -> str:
        """Gets the id of this Manifest.

        An identifier used to correlate this manifest with the selected plan and service. This MUST be globally unique within a platform marketplace. MUST be a non-empty string. Using a GUID is RECOMMENDED.   # noqa: E501

        :return: The id of this Manifest.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id: str):
        """Sets the id of this Manifest.

        An identifier used to correlate this manifest with the selected plan and service. This MUST be globally unique within a platform marketplace. MUST be a non-empty string. Using a GUID is RECOMMENDED.   # noqa: E501

        :param id: The id of this Manifest.
        :type id: str
        """
        if id is None:
            raise ValueError("Invalid value for `id`, must not be `None`")  # noqa: E501

        self._id = id

    @property
    def plan_id(self) -> str:
        """Gets the plan_id of this Manifest.

        The plan the manifest should be associated with  # noqa: E501

        :return: The plan_id of this Manifest.
        :rtype: str
        """
        return self._plan_id

    @plan_id.setter
    def plan_id(self, plan_id: str):
        """Sets the plan_id of this Manifest.

        The plan the manifest should be associated with  # noqa: E501

        :param plan_id: The plan_id of this Manifest.
        :type plan_id: str
        """
        if plan_id is None:
            raise ValueError("Invalid value for `plan_id`, must not be `None`")  # noqa: E501

        self._plan_id = plan_id

    @property
    def service_id(self) -> str:
        """Gets the service_id of this Manifest.

        The service type (id) the manifest should be assocaited with  # noqa: E501

        :return: The service_id of this Manifest.
        :rtype: str
        """
        return self._service_id

    @service_id.setter
    def service_id(self, service_id: str):
        """Sets the service_id of this Manifest.

        The service type (id) the manifest should be assocaited with  # noqa: E501

        :param service_id: The service_id of this Manifest.
        :type service_id: str
        """
        if service_id is None:
            raise ValueError("Invalid value for `service_id`, must not be `None`")  # noqa: E501

        self._service_id = service_id

    @property
    def manifest_type(self) -> str:
        """Gets the manifest_type of this Manifest.

        The type of system that that manifest targets  # noqa: E501

        :return: The manifest_type of this Manifest.
        :rtype: str
        """
        return self._manifest_type

    @manifest_type.setter
    def manifest_type(self, manifest_type: str):
        """Sets the manifest_type of this Manifest.

        The type of system that that manifest targets  # noqa: E501

        :param manifest_type: The manifest_type of this Manifest.
        :type manifest_type: str
        """
        if manifest_type is None:
            raise ValueError("Invalid value for `manifest_type`, must not be `None`")  # noqa: E501

        self._manifest_type = manifest_type

    @property
    def manifest_content(self) -> str:
        """Gets the manifest_content of this Manifest.

        The manifest content  # noqa: E501

        :return: The manifest_content of this Manifest.
        :rtype: str
        """
        return self._manifest_content

    @manifest_content.setter
    def manifest_content(self, manifest_content: str):
        """Sets the manifest_content of this Manifest.

        The manifest content  # noqa: E501

        :param manifest_content: The manifest_content of this Manifest.
        :type manifest_content: str
        """
        if manifest_content is None:
            raise ValueError("Invalid value for `manifest_content`, must not be `None`")  # noqa: E501

        self._manifest_content = manifest_content

    @property
    def endpoints(self) -> object:
        """Gets the endpoints of this Manifest.

        A set of endpoints that the service instance exposes. This includes APIs and UIs.  # noqa: E501

        :return: The endpoints of this Manifest.
        :rtype: object
        """
        return self._endpoints

    @endpoints.setter
    def endpoints(self, endpoints: object):
        """Sets the endpoints of this Manifest.

        A set of endpoints that the service instance exposes. This includes APIs and UIs.  # noqa: E501

        :param endpoints: The endpoints of this Manifest.
        :type endpoints: object
        """

        self._endpoints = endpoints

    @property
    def config(self) -> object:
        """Gets the config of this Manifest.

        configuration parameters to be supplied to a service instance. this is not service instance specific  # noqa: E501

        :return: The config of this Manifest.
        """
        return self._config

    @config.setter
    def config(self, config: object):

        """Sets the config of this Manifest.

        configuration parameters to be supplied to a service instance. this is not service instance specific  # noqa: E501
        """
        self._config = config
