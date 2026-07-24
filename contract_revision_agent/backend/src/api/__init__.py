"""API 层 — Flask JSON API 路由"""
from flask import Blueprint

api = Blueprint("api", __name__, url_prefix="/api")

from . import chat, contract, knowledge, config_api, upload
