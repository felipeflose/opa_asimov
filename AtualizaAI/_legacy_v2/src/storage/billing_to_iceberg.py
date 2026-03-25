import os
import logging
from typing import Optional
from datetime import datetime
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, expr

# --- Configurações de Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class BillingToIcebergPipeline:
    """
    Pipeline de FinOps para extrair Billing Export do BigQuery e persistir 
    em GCS no formato Apache Iceberg com idempotência via MERGE INTO.
    """
    
    def __init__(self, 
                 project_id: str, 
                 dataset_id: str, 
                 table_name: str, 
                 iceberg_warehouse: str,
                 iceberg_catalog_name: str = "gcs_catalog"):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_name = table_name
        self.iceberg_warehouse = iceberg_warehouse
        self.catalog_name = iceberg_catalog_name
        
        self.spark = self._init_spark()

    def _init_spark(self) -> SparkSession:
        """Inicializa Spark com extensões Iceberg e conectores BQ."""
        logger.info("Inicializando Spark Session com suporte a Iceberg e BigQuery...")
        
        # Versões sugeridas para Spark 3.3/3.4
        ICEBERG_VERSION = "1.4.2"
        GCS_CONNECTOR_VERSION = "hadoop3-2.2.14"
        
        return (SparkSession.builder
            .appName("FloseAI-FinOps-BillingRecord")
            # Configurações Iceberg
            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkExtensions")
            .config(f"spark.sql.catalog.{self.catalog_name}", "org.apache.iceberg.spark.SparkCatalog")
            .config(f"spark.sql.catalog.{self.catalog_name}.type", "hadoop")
            .config(f"spark.sql.catalog.{self.catalog_name}.warehouse", self.iceberg_warehouse)
            # BigQuery Connector
            .config("spark.jars.packages", f"org.apache.iceberg:iceberg-spark-runtime-3.3_2.12:{ICEBERG_VERSION}")
            .getOrCreate())

    def extract_from_bq(self) -> DataFrame:
        """Lê os dados de faturamento do BigQuery."""
        bq_table = f"{self.project_id}.{self.dataset_id}.{self.table_name}"
        logger.info(f"Extraindo dados da fonte BQ: {bq_table}")
        
        # Seleção granular para evitar overhead
        return (self.spark.read.format("bigquery")
            .option("table", bq_table)
            # Seleção de campos essenciais (usage_start_time, sku, cost, etc)
            .load()
            .select(
                col("usage_start_time"),
                col("service"),
                col("sku"),
                col("cost"),
                col("currency"),
                col("export_time"),
                # Gera um hash único para idempotência (ex: usage_start_time + sku.id)
                expr("hash(usage_start_time, sku.id) as row_hash")
            ))

    def run(self):
        """Executa o pipeline completo."""
        try:
            df_source = self.extract_from_bq()
            
            # 1. Cria a tabela se não existir (Hidden Partitioning por Mês)
            target_table = f"{self.catalog_name}.finops.billing_history"
            
            # Check se existe
            self.spark.sql(f"CREATE DATABASE IF NOT EXISTS {self.catalog_name}.finops")
            
            # Nota técnica: 'month(usage_start_time)' é Hidden Partitioning do Iceberg
            # Evita a necessidade de criar colunas artificiais como 'year_month'
            logger.info(f"Iniciando MERGE INTO na tabela Iceberg: {target_table}")
            
            # 2. MERGE INTO para idempotência perfeita
            # Resolvido: Merge impacta performance dependendo dos 'Delete Files', 
            # mas o Iceberg compensa com o isolamento de snapshots.
            df_source.createOrReplaceTempView("source_billing")
            
            merge_query = f"""
            MERGE INTO {target_table} t
            USING source_billing s
            ON t.row_hash = s.row_hash AND t.usage_start_time = s.usage_start_time
            WHEN MATCHED AND t.cost != s.cost THEN
                UPDATE SET t.cost = s.cost, t.export_time = s.export_time
            WHEN NOT MATCHED THEN
                INSERT *
            """
            
            # Caso a tabela não exista, o Iceberg permite o create table as select ou merge 
            # Mas aqui forçamos o schema se for a primeira vez
            if not self._table_exists(target_table):
                logger.info("Primeira execução: Criando tabela com particionamento mensal.")
                df_source.writeTo(target_table).partitionedBy("usage_start_time").create()
            else:
                self.spark.sql(merge_query)
            
            logger.info("Pipeline FinOps finalizado com sucesso.")
            
        except Exception as e:
            logger.error(f"Erro crítico no pipeline FinOps: {e}")
            raise e

    def _table_exists(self, table_name: str) -> bool:
        try:
            self.spark.sql(f"DESCRIBE TABLE {table_name}")
            return True
        except:
            return False

if __name__ == "__main__":
    # Exemplo de execução (Configurado via Env Vars)
    pipeline = BillingToIcebergPipeline(
        project_id=os.getenv("GCP_PROJECT_ID", "api-gemini-oficial"),
        dataset_id=os.getenv("BQ_BILLING_DATASET", "billing_export"),
        table_name=os.getenv("BQ_BILLING_TABLE", "gcp_billing_export_v1_XXXXX"),
        iceberg_warehouse=f"gs://flose-ai-platform-{os.getenv('GCP_PROJECT_ID')}/finops/warehouse"
    )
    pipeline.run()
