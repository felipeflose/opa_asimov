import os
import ast
import subprocess
import sys
import pkgutil

# Configurações de caminhos
PATH_PROJETO = r'C:\Users\fflose\flose\opa_asimov'
PATH_REQUIREMENTS = os.path.join(PATH_PROJETO, 'requirements.txt')
PATH_VENV_PIP = r'C:\Users\fflose\flose\.venv\Scripts\pip.exe'

def buscar_bibliotecas_padrao():
    """Lista módulos nativos para não colocar no requirements.txt"""
    std_libs = {m.name for m in pkgutil.iter_modules()}
    std_libs.update(sys.builtin_module_names)
    # Adicionais que às vezes passam pelo filtro
    std_libs.update(['__future__', 'os', 'sys', 'ast', 'subprocess', 'json', 'time', 'datetime', 're'])
    return std_libs

def extrair_imports(diretorio):
    libs_encontradas = set()
    std_libs = buscar_bibliotecas_padrao()
    
    for raiz, _, arquivos in os.walk(diretorio):
        # Pula pastas de ambiente virtual e cache
        if any(x in raiz for x in ['.venv', '__pycache__', '.git', '.ipynb_checkpoints']):
            continue
            
        for arquivo in arquivos:
            # IGNORA arquivos que começam com "._" ou que não terminam em ".py"
            if arquivo.startswith('._') or not arquivo.endswith('.py'):
                continue
                
            caminho_completo = os.path.join(raiz, arquivo)
            try:
                # 'errors="ignore"' evita crash com caracteres estranhos
                with open(caminho_completo, 'r', encoding='utf-8', errors='ignore') as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        lib = None
                        if isinstance(node, ast.Import):
                            for n in node.names:
                                lib = n.name.split('.')[0]
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                lib = node.module.split('.')[0]
                        
                        if lib and lib not in std_libs:
                            # Verifica se não é um arquivo local (.py na mesma pasta)
                            if not os.path.exists(os.path.join(raiz, f"{lib}.py")):
                                libs_encontradas.add(lib)
            except Exception as e:
                print(f"⚠️ Pulando {arquivo}: {e}")
    
    return sorted(list(libs_encontradas))

def salvar_requirements(libs, caminho):
    if not libs:
        return False
    with open(caminho, 'w', encoding='utf-8') as f:
        for lib in libs:
            f.write(f"{lib}\n")
    print(f"✅ Arquivo requirements.txt limpo e gerado em: {caminho}")
    return True

def instalar_libs(caminho_requirements, pip_path):
    print(f"🚀 Verificando bibliotecas no ambiente: {pip_path}")
    if not os.path.exists(caminho_requirements): return

    try:
        # Usamos --disable-pip-version-check para menos poluição visual
        subprocess.check_call([pip_path, 'install', '-r', caminho_requirements, '--disable-pip-version-check'])
        print("✅ Tudo pronto! Bibliotecas instaladas/verificadas.")
    except Exception as e:
        print(f"❌ Erro na instalação: {e}")

if __name__ == "__main__":
    print("🔍 Analisando seu código (ignorando arquivos temporários e nativos)...")
    bibliotecas = extrair_imports(PATH_PROJETO)
    
    if salvar_requirements(bibliotecas, PATH_REQUIREMENTS):
        instalar_libs(PATH_REQUIREMENTS, PATH_VENV_PIP)
    else:
        print("Nenhuma biblioteca externa encontrada para instalar.")