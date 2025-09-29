from flask import Flask, render_template, request, jsonify
from models import Database, Categoria, Habito

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu-secret-key-segura-aqui'

# Inicializar base de datos
db = Database()
db.seed_data()

@app.route('/')
@app.route('/explorar')
def explorar():
    """Página principal de exploración de hábitos"""
    categorias = Categoria.get_all()
    habitos = Habito.get_all()
    return render_template('explorar.html', categorias=categorias, habitos=habitos)

@app.route('/habito/<int:habito_id>')
def detalle_habito(habito_id):
    """Página de detalle de un hábito específico"""
    habito = Habito.get_by_id(habito_id)
    if not habito:
        return render_template('404.html'), 404
    return render_template('detalle_habito.html', habito=habito)

@app.route('/api/habitos/categoria/<int:categoria_id>')
def api_habitos_por_categoria(categoria_id):
    """API para obtener hábitos filtrados por categoría"""
    habitos = Habito.get_by_categoria(categoria_id)
    return jsonify(habitos)

@app.route('/api/habitos/buscar')
def api_buscar_habitos():
    """API para buscar hábitos por texto"""
    query = request.args.get('q', '')
    if not query:
        habitos = Habito.get_all()
    else:
        habitos = Habito.search(query)
    return jsonify(habitos)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)