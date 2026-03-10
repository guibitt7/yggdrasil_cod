# mock_ygg_logs.py
import uuid
import time

from yggdrasil.logger.models import (
    ParamsLogger,
    LevelLogEnum,
    StatusAutomationEnum,
)
from yggdrasil.logger.ygg_logger import YggLogger


def simular_robo_credito():
    params = ParamsLogger(
        exec_id=uuid.uuid4(),
        automation_name="robo_contratacao_credito",
        process_name="Credito Pessoal",
        fluid_id=1001,
        impersonal_user="svc_rpa_credito",
    )
    ygg = YggLogger(params)

    ygg.log_start("Iniciando contratação de crédito")
    time.sleep(0.05)

    ygg.log(
        LevelLogEnum.INFO,
        "Login Portal",
        "Acesso ao portal realizado com sucesso",
    )
    ygg.log(
        LevelLogEnum.DEBUG,
        "Lendo Fila",
        "12 contratos encontrados na fila",
    )
    ygg.log(
        LevelLogEnum.INFO,
        "Processando",
        "Processando contrato #1001",
    )
    ygg.log(
        LevelLogEnum.WARNING,
        "Timeout",
        "Portal lento, aguardando 5s",
        status=StatusAutomationEnum.RETRYING,
    )
    ygg.log(
        LevelLogEnum.INFO,
        "Processando",
        "Contrato #1001 aprovado",
    )

    ygg.log_finish(
        StatusAutomationEnum.SUCCESS,
        "Finalizado",
        "Todos os contratos processados",
    )


def simular_robo_nfe():
    params = ParamsLogger(
        exec_id=uuid.uuid4(),
        automation_name="robo_extracao_nfe",
        process_name="Fiscal",
        fluid_id=2042,
        impersonal_user="svc_rpa_fiscal",
    )
    ygg = YggLogger(params)

    ygg.log_start("Abrindo sistema fiscal")
    time.sleep(0.05)

    ygg.log(
        LevelLogEnum.INFO,
        "Login SEFAZ",
        "Certificado digital validado",
    )
    ygg.log(
        LevelLogEnum.INFO,
        "Download XML",
        "Baixando 87 NF-es do período",
    )
    ygg.log(
        LevelLogEnum.ERROR,
        "Parsing XML",
        "NF-e #55123 com schema inválido",
        error_type="XMLParseError",
    )
    ygg.log(
        LevelLogEnum.WARNING,
        "Continuando",
        "Pulando NF-e inválida e continuando",
    )
    ygg.log(
        LevelLogEnum.INFO,
        "Salvando",
        "86 NF-es salvas com sucesso",
    )

    ygg.log_finish(
        StatusAutomationEnum.SUCCESS,
        "Finalizado",
        "Extração concluída com 1 erro ignorado",
    )


def simular_robo_relatorio_falha():
    params = ParamsLogger(
        exec_id=uuid.uuid4(),
        automation_name="robo_relatorio_gerencial",
        process_name="Controladoria",
        fluid_id=3099,
        impersonal_user="svc_rpa_ctrl",
    )
    ygg = YggLogger(params)

    ygg.log_start("Abrindo Excel para relatório")
    time.sleep(0.05)

    ygg.log(
        LevelLogEnum.INFO,
        "Conectando BD",
        "Conexão com banco de dados estabelecida",
    )
    ygg.log(
        LevelLogEnum.INFO,
        "Extraindo Dados",
        "Consultando dados do mês",
    )
    ygg.log(
        LevelLogEnum.CRITICAL,
        "Erro Fatal",
        "Banco de dados retornou timeout após 3 tentativas",
        error_type="DBTimeoutError",
    )

    ygg.log_finish(
        StatusAutomationEnum.FAILED,
        "Abortado",
        "Relatório não gerado por falha no BD",
        error_type="DBTimeoutError",
    )


def main():
    print("=" * 60)
    print(" GERANDO LOGS MOCK DO YGGDRASIL ")
    print("=" * 60)

    simular_robo_credito()
    simular_robo_nfe()
    simular_robo_relatorio_falha()

    print("\nLogs gerados. Verifique o arquivo de log configurado no LogWriter.")
    print("Se estiver no Mac, deve estar em algo como:")
    print("  ~/Documents/Yggdrasil/Logs/<ROBOT>_<YYYY-MM-DD>.log")


if __name__ == "__main__":
    main()
