# votoAppWSServer/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.forms.models import model_to_dict

from .models import Censo, Voto
from .serializers import CensoSerializer, VotoSerializer
from .votoDB import verificar_censo, registrar_voto, eliminar_voto, get_votos_from_db


class CensoView(APIView):
    """
    POST /restapiserver/censo/
     - recibe JSON con los datos necesarios para comprobar en el censo
     - 200 si existe, 404 si no existe, 400 si JSON inválido
    """
    def post(self, request, format=None):
        serializer = CensoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # verificar_censo espera un dict con los datos del serializer
        if verificar_censo(serializer.validated_data):
            return Response({'message': 'Votante autorizado'}, status=status.HTTP_200_OK)
        return Response(
            {'message': 'Datos no encontrados en Censo.'},
            status=status.HTTP_404_NOT_FOUND
        )


class VotoView(APIView):
    """
    POST   /restapiserver/voto/
      - recibe JSON con datos del voto (incluye campo censo que es el numeroDNI)
      - 200 + objeto voto registrado si OK
      - 404 si el censo no existe
      - 400 en cualquier otro error o JSON inválido

    DELETE /restapiserver/voto/<id_voto>/
      - elimina voto por su id
      - 200 si lo borró, 404 si no lo encontró
    """
    def post(self, request, format=None):
        serializer = VotoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        voto = registrar_voto(serializer.validated_data)
        if voto is None:
            # registrar_voto hace catch genérico, puede ser fallo de FK en censo
            return Response({'message': 'Error al registrar voto.'}, status=status.HTTP_400_BAD_REQUEST)

        # devuelve el voto creado en JSON
        return Response(model_to_dict(voto), status=status.HTTP_200_OK)

    def delete(self, request, id_voto, format=None):
        if eliminar_voto(id_voto):
            return Response({'message': 'Voto eliminado'}, status=status.HTTP_200_OK)
        return Response({'message': 'Voto no encontrado'}, status=status.HTTP_404_NOT_FOUND)


class ProcesoElectoralView(APIView):
    """
    GET /restapiserver/procesoelectoral/<idProcesoElectoral>/
      - lista todos los votos del proceso electoral dado
      - 200 + lista si hay al menos uno
      - 404 si no hay ninguno
    """
    def get(self, request, idProcesoElectoral, format=None):
        votos = get_votos_from_db(idProcesoElectoral)
        if votos.exists():
            serializer = VotoSerializer(votos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'message': 'No se encontraron votos'}, status=status.HTTP_404_NOT_FOUND)
