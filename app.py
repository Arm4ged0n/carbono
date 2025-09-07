from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# =============================================================================
# CALCULADORA DE PEGADA DE CARBONO: VERSAO PROFISSIONAL E INTERATIVA
# =============================================================================

app = Flask(__name__)
CORS(app)  # Permite que o front-end (HTML) se comunique com este servidor

# Dicionario com fatores de emissao (valores em kg de CO2e por unidade)
FATORES_EMISSAO = {
    # Energia Residencial
    "eletricidade_kwh_brasil": 0.12,  # kg CO2e por kWh
    "gas_encanado_m3": 2.0,           # kg CO2e por m3
    "gas_botijao_kg": 3.0,            # kg CO2e por kg
    "media_residente_por_m2": 0.05,   # Fator de pegada media por m2 de residencia

    # Transporte
    "carro_gasolina_km": 0.23,
    "carro_etanol_km": 0.08,
    "onibus_km_passageiro": 0.08,
    "metro_km_passageiro": 0.03,
    "moto_km_gasolina": 0.1,

    # Alimentacao
    "carne_vermelha_semana": 10,
    "aves_porco_semana": 5,
    "peixe_semana": 3,
    "dieta_vegetariana_semana": 1.5,
    "dieta_vegana_semana": 0.5,

    # Consumo e Residuos
    "residuo_kg_por_pessoa": 0.5,
    "vestuario_anual": 150,
}

# Fator de conversao: 1 credito de carbono = 1 tonelada de CO2e
FATOR_CREDITO = 1000  # kg para tonelada

@app.route('/')
def home():
    return render_template('carbono.html')

@app.route('/calcular_pegada', methods=['POST'])
def calcular_pegada():
    try:
        data = request.json

        # Converte os valores de string para int ou float
        num_residentes = int(data.get('num_residentes', 0))
        area_casa = float(data.get('area_casa', 0))
        consumo_kwh = float(data.get('consumo_energia_kwh', 0))
        consumo_gas = float(data.get('consumo_gas_m3', 0))
        
        km_carro = float(data.get('km_carro_mensal', 0))
        tipo_combustivel = data.get('tipo_combustivel', 'gasolina')
        km_onibus = float(data.get('km_onibus_mensal', 0))
        km_metro = float(data.get('km_metro_mensal', 0))

        dieta_tipo = data.get('dieta_tipo', 'carnivora')
        residuos_kg = float(data.get('residuos_kg_semana', 0))

        # Cálculos
        co2_energia = 0
        if num_residentes > 0:
            co2_energia = (area_casa * FATORES_EMISSAO["media_residente_por_m2"]) / num_residentes
        co2_energia += (consumo_kwh * 12 * FATORES_EMISSAO["eletricidade_kwh_brasil"])
        co2_energia += (consumo_gas * 12 * FATORES_EMISSAO["gas_encanado_m3"])

        co2_transporte = 0
        if tipo_combustivel == 'etanol':
            co2_transporte += (km_carro * 12) * FATORES_EMISSAO["carro_etanol_km"]
        else:
            co2_transporte += (km_carro * 12) * FATORES_EMISSAO["carro_gasolina_km"]
        co2_transporte += (km_onibus * 12) * FATORES_EMISSAO["onibus_km_passageiro"]
        co2_transporte += (km_metro * 12) * FATORES_EMISSAO["metro_km_passageiro"]

        co2_alimentacao = 0
        if dieta_tipo == 'carnivora':
            co2_alimentacao = 52 * FATORES_EMISSAO["carne_vermelha_semana"] * 3
        elif dieta_tipo == 'vegetariana':
            co2_alimentacao = 52 * FATORES_EMISSAO["dieta_vegetariana_semana"]
        elif dieta_tipo == 'vegana':
            co2_alimentacao = 52 * FATORES_EMISSAO["dieta_vegana_semana"]

        co2_residuos_consumo = (residuos_kg * 52) * FATORES_EMISSAO["residuo_kg_por_pessoa"]
        co2_residuos_consumo += FATORES_EMISSAO["vestuario_anual"]

        co2_total_kg = co2_energia + co2_transporte + co2_alimentacao + co2_residuos_consumo
        co2_total_toneladas = co2_total_kg / FATOR_CREDITO
        creditos_a_compensar = co2_total_toneladas

        return jsonify({
            "total_toneladas": f"{co2_total_toneladas:.2f}",
            "creditos_compensar": f"{creditos_a_compensar:.2f}",
            "quebra": {
                "energia": f"{co2_energia / 1000:.2f}",
                "transporte": f"{co2_transporte / 1000:.2f}",
                "alimentacao": f"{co2_alimentacao / 1000:.2f}",
                "residuos": f"{co2_residuos_consumo / 1000:.2f}"
            }
        })

    except Exception as e:
        return jsonify({"erro": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
