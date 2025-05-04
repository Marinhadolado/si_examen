from rest_framework import serializers
from . models import Voto, Censo, CodigoRespuesta

class VotoSerializer(serializers.ModelSerializer):
    """Serializador para el modelo Voto"""
    class Meta:
        model = Voto
        fields = '__all__'
        read_only_fields = ['marcaTiempo', 'codigoRespuesta']
        extra_kwargs = {
            'idCircunscripcion': {'required': True},
            'idMesaElectoral': {'required': True},
            'idProcesoElectoral': {'required': True},
            'nombreCandidatoVotado': {'required': True},
            'censo': {'required': True}
        }
        
    def create(self, validated_data):
        """Sobrescribimos el método create para manejar la creación de votos"""
        # Aquí puedes agregar lógica adicional si es necesario
        return super().create(validated_data)

class CensoSerializer(serializers.ModelSerializer):
    """Serializador para el modelo Censo"""
    class Meta:
        model = Censo
        fields = '__all__'
        read_only_fields = ['numeroDNI']
        extra_kwargs = {
            'nombre': {'required': True},
            'fechaNacimiento': {'required': True},
            'anioCenso': {'required': True},
            'codigoAutorizacion': {'required': True}
        }

class CodigoRespuestaSerializer(serializers.ModelSerializer):
    """Serializador para el modelo CodigoRespuesta"""
    class Meta:
        model = CodigoRespuesta
        fields = '__all__'
        read_only_fields = ['codigoRespuesta']
        extra_kwargs = {
            'codigoRespuesta': {'required': True}
        }

