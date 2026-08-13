from fastapi.templating import Jinja2Templates
from fastapi import templating

template = templating.Jinja2Templates(
    directory="templates"
)
