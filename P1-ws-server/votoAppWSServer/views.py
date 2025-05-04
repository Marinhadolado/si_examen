# votoAppWSServer/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Censo, Voto
from django.forms.models import model_to_dict
from django.utils.timezone import now
from .serializers import VotoSerializer


from django.shortcuts import redirect, render
from .forms import VotoForm, CensoForm, DelVotoForm, GetVotosForm
from .votoDB import (verificar_censo, registrar_voto,
                            eliminar_voto, get_votos_from_db)


def testbd(request):

    if request.method == 'POST':
        voto_form = VotoForm(request.POST)
        censo_form = CensoForm(request.POST)

        if not voto_form.is_valid() or not censo_form.is_valid():
            return render(
                request, 'template_mensaje.html',
                {'mensaje': '¡Error: Datos inválidos!', 'title': TITLE}
            )

        if not verificar_censo(censo_form.cleaned_data):
            return render(
                request, 'template_mensaje.html',
                {'mensaje': '¡Error: Votante no registrado en el Censo!', 'title': TITLE}
            )

        voto_data = voto_form.cleaned_data
        censo_data = censo_form.cleaned_data

        voto_data['censo_id'] = censo_data['numeroDNI']

        voto = registrar_voto(voto_data)

        if voto is None:
            return render(
                request, 'template_mensaje.html',
                {'mensaje': 'Error al registrar voto!', 'title': TITLE}
            )

        context_dict = {'voto': voto, 'title': TITLE}
        return render(request, 'template_exito.html', context_dict)

    else:
        voto_form = VotoForm()
        censo_form = CensoForm()

        return render(request, 'template_test_bd.html', {
            'voto_form': voto_form,
            'censo_form': censo_form,
            'title': TITLE
        })



class CensoView(APIView):
    """
    POST /restapiserver/censo/
     - recibe JSON con los datos necesarios para comprobar en el censo
     - 200 si existe, 404 si no existe, 400 si JSON inválido
    """
    def post(self, request, format=None):
        numeroDNI = request.data.get('numeroDNI')
        nombre = request.data.get('nombre')
        fechaNacimiento = request.data.get('fechaNacimiento')
        anioCenso = request.data.get('anioCenso')
        codigoAutorizacion = request.data.get('codigoAutorizacion')

        if not any([numeroDNI, nombre, fechaNacimiento, anioCenso, codigoAutorizacion]):
            return Response(
                {'message': 'Debe proporcionar al menos un dato para buscar en el censo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        filtro = {}
        if numeroDNI:
            filtro['numeroDNI'] = numeroDNI
        if nombre:
            filtro['nombre'] = nombre
        if fechaNacimiento:
            filtro['fechaNacimiento'] = fechaNacimiento
        if anioCenso:
            filtro['anioCenso'] = anioCenso
        if codigoAutorizacion:
            filtro['codigoAutorizacion'] = codigoAutorizacion

        coincidencias = Censo.objects.filter(**filtro)

        if coincidencias.exists():
            coincidencias_list = list(coincidencias.values())
            return Response(
                {'message': 'Datos encontrados en Censo.'},
                status=status.HTTP_200_OK
            )

        return Response({'message': 'Datos no encontrados en Censo.'}, status=status.HTTP_404_NOT_FOUND)



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
        voto_form = VotoForm(request.data)

        if not voto_form.is_valid():
            return Response({'message': 'Datos inválidos', 'errors': voto_form.errors}, status=status.HTTP_400_BAD_REQUEST)

        numero_dni = request.data.get('censo_id')
        id_proceso = request.data.get('idProcesoElectoral')
        id_circunscripcion = request.data.get('idCircunscripcion')
        id_mesa = request.data.get('idMesaElectoral')
        opcion = request.data.get('nombreCandidatoVotado')
        try:
            votante = Censo.objects.get(numeroDNI=numero_dni)
        except Censo.DoesNotExist:
            return Response({'message': 'Votante no encontrado en el censo.'}, status=status.HTTP_404_NOT_FOUND)

        if Voto.objects.filter(censo=votante, idProcesoElectoral=id_proceso).exists():
            return Response({'message': 'El votante ya ha emitido un voto en este proceso electoral.'}, status=status.HTTP_400_BAD_REQUEST)

        voto_dict = {
            'censo': votante,
            'idProcesoElectoral': id_proceso,
            'idCircunscripcion': id_circunscripcion,
            'idMesaElectoral': id_mesa,
            'nombreCandidatoVotado': opcion,
            'marcaTiempo': now(),
            'codigoRespuesta': "200"
        }

        voto = registrar_voto(voto_dict)

        if voto is None:
            return Response({'message': 'voto es none!'}, status=status.HTTP_400_BAD_REQUEST)


        voto_dict = model_to_dict(voto)
        voto_dict['censo_id'] = votante.numeroDNI

        return Response(voto_dict, status=status.HTTP_200_OK)

    def delete(self, request, id_voto, format=None):
        """Eliminar un voto por ID"""
        if not id_voto:
            return Response({'message': 'ID del voto requerido.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            voto = Voto.objects.get(id=id_voto)
            voto.delete()
            return Response({'message': 'Voto eliminado correctamente.'}, status=status.HTTP_200_OK)
        except Voto.DoesNotExist:
            return Response({'message': 'Voto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)


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
