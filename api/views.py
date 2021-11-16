import io
import json

from django.shortcuts import render

from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NSFWModel, ImageBinary, ImageUrl


# Create your views here.
class Predict(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request):
        if not NSFWModel.is_ready():
            return Response({}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({}, status=status.HTTP_200_OK)

    def post(self, request):
        if request.content_type.startswith('application/json'):
            # Json request
            if not request.body:
                return Response({'valid': {}, 'invalid': {}, 'error': 'Invalid json request'})
            IProcessor = ImageUrl
        elif request.content_type.startswith('multipart/form-data'):
            # Form request
            if not request.FILES:
                return Response({'valid': {}, 'invalid': {}, 'error': 'Invalid form request'})
            IProcessor = ImageBinary
        else:
            # Invalid mimetype
            return Response({'valid': {}, 'invalid': {}, 'error': 'Invalid request'})
        try:
            valid_images, invalid_images = IProcessor.prepare(request)
            json_valid = {}
            json_invalid = dict(zip(*zip(*invalid_images))) if len(invalid_images) > 0 else {}
            if len(valid_images) > 0:
                image_names, images = zip(*valid_images)
                results = NSFWModel.predict(images)
                json_valid = dict(zip(image_names, results))
            json_data = {
                'valid': json_valid,
                'invalid': json_invalid,
            }
            return Response(json_data)
        except json.decoder.JSONDecodeError as exc:
            return Response({'valid': {}, 'invalid': {}, 'error': f'Invalid json data: {exc}'})
        except Exception as exc:
            return Response({'valid': {}, 'invalid': {}, 'error': str(exc)})
