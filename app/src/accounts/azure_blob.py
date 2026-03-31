# -*- coding: utf-8 -*-
from django.conf import settings
from azure.storage.blob import BlobServiceClient
from loguru import logger


def get_blob_service_client():
    return BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)


def get_user_container_name(user):
    """Return a deterministic container name for a user."""
    return f"user-{user.id}"


def ensure_user_container(user):
    """Create a blob container for the user if it doesn't exist."""
    client = get_blob_service_client()
    container_name = get_user_container_name(user)
    try:
        client.create_container(container_name)
        logger.info(f"Created blob container: {container_name}")
    except Exception as e:
        if "ContainerAlreadyExists" in str(e):
            pass
        else:
            logger.error(f"Failed to create container {container_name}: {e}")
            raise
    return container_name


def upload_blob(user, file_name, file_data):
    """Upload a file to the user's blob container. Returns the blob URL."""
    container_name = ensure_user_container(user)
    client = get_blob_service_client()
    blob_client = client.get_blob_client(container=container_name, blob=file_name)
    blob_client.upload_blob(file_data, overwrite=True)
    logger.info(f"Uploaded blob: {container_name}/{file_name}")
    return blob_client.url


def download_blob(user, file_name):
    """Download a blob and return its bytes and content type."""
    container_name = get_user_container_name(user)
    client = get_blob_service_client()
    blob_client = client.get_blob_client(container=container_name, blob=file_name)
    stream = blob_client.download_blob()
    properties = blob_client.get_blob_properties()
    return stream.readall(), properties.content_settings.content_type


def list_blobs(user):
    """List all blobs in a user's container."""
    container_name = get_user_container_name(user)
    client = get_blob_service_client()
    container_client = client.get_container_client(container_name)
    try:
        return list(container_client.list_blobs())
    except Exception:
        return []


def delete_blob(user, file_name):
    """Delete a blob from the user's container."""
    container_name = get_user_container_name(user)
    client = get_blob_service_client()
    blob_client = client.get_blob_client(container=container_name, blob=file_name)
    blob_client.delete_blob()
    logger.info(f"Deleted blob: {container_name}/{file_name}")
