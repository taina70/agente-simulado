import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Definimos o contrato de saída (Structured Output)
# Isso garante que o front-end nunca vai quebrar por resposta fora de padrão
class Questao(BaseModel):
    enunciado: str = Field(description="O texto base e o comando da questão no estilo da banca")
    alternativas: list[str] = Field(description="Lista com 5 alternativas (A a E) ou 2 (Certo/Errado)")
    gabarito: str = Field(description="A resposta correta exata")
    justificativa: str = Field(description="Explicação detalhada citando a lei ou regra")
    topico: str = Field(description="O assunto específico abordado na questão")

class Simulado(BaseModel):
    banca: str
    materia: str
    questoes: list[Questao]

# 2. Criamos uma Ferramenta (Tool) para o Agente
# Aqui simulamos uma consulta ao seu PostgreSQL/SQLite de histórico de estudos
def buscar_pontos_fracos(materia: str) -> dict:
    """Consulta o banco de dados do aluno para descobrir os tópicos com maior taxa de erro."""
    historico_simulado = {
        "Direito Constitucional": ["Controle de Constitucionalidade", "Direitos e Garantias Fundamentais (Art. 5º)"],
        "Informática": ["Segurança da Informação", "Redes de Computadores e Protocolos"],
        "Português": ["Crase", "Concordância Verbal e Nominal"]
    }
    topicos = historico_simulado.get(materia, ["Tópicos Gerais do Edital"])
    return {"materia": materia, "topicos_com_mais_erros": topicos}

# 3. Inicializamos o cliente do Gemini
client = genai.Client()

def gerar_simulado_personalizado(materia: str, banca: str, quantidade: int = 3) -> Simulado:
    prompt = f"""
    Você é um especialista em elaboração de provas de concursos públicos.
    Antes de criar as questões, consulte obrigatoriamente o histórico de pontos fracos do aluno 
    para a matéria '{materia}' usando a ferramenta disponível.
    Depois, gere {quantidade} questões inéditas no estilo rigoroso da banca {banca}, 
    focando prioritariamente nos tópicos que o aluno mais erra.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[buscar_pontos_fracos], # Damos a ferramenta ao agente
            response_mime_type="application/json",
            response_schema=Simulado,     # Exigimos a saída tipada
            temperature=0.3               # Baixa criatividade para manter rigor técnico
        ),
    )

    # O SDK já retorna o texto pronto para ser convertido no objeto Pydantic
    return Simulado.model_validate_json(response.text)

# Testando na prática
if __name__ == "__main__":
    resultado = gerar_simulado_personalizado(materia="Direito Constitucional", banca="Cebraspe", quantidade=2)
    print(resultado.model_dump_json(indent=2))
