"""
Estimador de datas genealógicas (nascimento/casamento) a partir de premissas
heurísticas configuráveis.

As premissas padrão NÃO são uma norma oficial do FamilySearch — são heurísticas
genealógicas comuns. Ajuste por época e região antes de aplicar em massa.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Premissas:
    """Premissas de estimativa. Ajuste por época e região antes de usar."""
    idade_homem_casamento: int = 25
    idade_mulher_casamento: int = 21
    tolerancia: int = 5                # margem de erro em anos, para cima e para baixo
    intervalo_primeiro_filho: int = 1  # anos entre casamento e nascimento do 1º filho
    intervalo_entre_filhos: int = 2
    idade_max_mae_parto: int = 45
    idade_min_mae_parto: int = 12


@dataclass(frozen=True)
class Estimativa:
    ano: int
    minimo: int
    maximo: int

    def gedcom(self) -> str:
        """Data no formato GEDCOM, com o qualificador ABT (aproximado)."""
        return f"ABT {self.ano}"

    def __str__(self) -> str:
        return f"ABT {self.ano} (faixa {self.minimo}\u2013{self.maximo})"


class EstimadorGenealogico:
    """Estima anos de nascimento/casamento a partir de um dado parcial conhecido.

    Nunca substitui uma data já documentada — use apenas para pessoas sem
    BIRT/DATE (ou MARR/DATE) no GEDCOM.
    """

    def __init__(self, premissas: "Premissas | None" = None):
        self.p = premissas or Premissas()

    @staticmethod
    def _validar_ano(ano: int) -> None:
        if not (1000 <= ano <= 2100):
            raise ValueError(f"Ano fora do intervalo plausível: {ano}")

    def _faixa(self, ano: int) -> Estimativa:
        t = self.p.tolerancia
        return Estimativa(ano, ano - t, ano + t)

    def nascimentos_a_partir_do_casamento(self, ano_casamento: int) -> dict:
        """Estima nascimento dos cônjuges e do 1º filho a partir do ano de casamento."""
        self._validar_ano(ano_casamento)
        return {
            "casamento": self._faixa(ano_casamento),
            "marido": self._faixa(ano_casamento - self.p.idade_homem_casamento),
            "esposa": self._faixa(ano_casamento - self.p.idade_mulher_casamento),
            "primeiro_filho": self._faixa(
                ano_casamento + self.p.intervalo_primeiro_filho
            ),
        }

    def casamento_a_partir_do_primeiro_filho(
        self, ano_filho: int, ano_nasc_mae: "int | None" = None
    ) -> dict:
        """Estima casamento e nascimento dos pais a partir do 1º filho.

        Se o ano de nascimento da mãe já for conhecido, calcula a idade dela
        no parto e sinaliza em 'alerta_idade_parto' se estiver fora da faixa
        biologicamente plausível (ver Premissas.idade_min/max_mae_parto).
        """
        self._validar_ano(ano_filho)
        ano_casamento = ano_filho - self.p.intervalo_primeiro_filho
        resultado = {
            "casamento": self._faixa(ano_casamento),
            "marido": self._faixa(ano_casamento - self.p.idade_homem_casamento),
            "esposa": self._faixa(ano_casamento - self.p.idade_mulher_casamento),
        }
        if ano_nasc_mae is not None:
            idade_parto = ano_filho - ano_nasc_mae
            resultado["idade_mae_no_parto"] = idade_parto
            resultado["alerta_idade_parto"] = not (
                self.p.idade_min_mae_parto <= idade_parto <= self.p.idade_max_mae_parto
            )
        return resultado

    def projetar_filhos(self, ano_primeiro_filho: int, total: int) -> list:
        """Projeta o ano aproximado de nascimento de cada filho, com faixa própria."""
        self._validar_ano(ano_primeiro_filho)
        filhos = []
        for i in range(total):
            ano = ano_primeiro_filho + i * self.p.intervalo_entre_filhos
            filhos.append(self._faixa(ano))
        return filhos


if __name__ == "__main__":
    est = EstimadorGenealogico()

    print("--- Casamento em 1920 ---")
    for papel, estim in est.nascimentos_a_partir_do_casamento(1920).items():
        print(f"  {papel}: {estim}  | GEDCOM: {estim.gedcom()}")

    print("\n--- 1º filho em 1921, mãe nascida em 1898 ---")
    for chave, valor in est.casamento_a_partir_do_primeiro_filho(
        1921, ano_nasc_mae=1898
    ).items():
        print(f"  {chave}: {valor}")

    print("\n--- Projeção de 4 filhos a partir de 1921 ---")
    for i, f in enumerate(est.projetar_filhos(1921, 4), 1):
        print(f"  {i}\u00ba filho: {f}  | GEDCOM: {f.gedcom()}")
