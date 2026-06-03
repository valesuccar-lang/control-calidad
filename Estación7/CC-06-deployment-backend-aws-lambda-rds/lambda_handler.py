"""AWS Lambda entry point using Mangum adapter"""
from mangum import Mangum
from app.main import app

handler = Mangum(app, lifespan="off")
