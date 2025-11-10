from flask import Blueprint, render_template

manage_bp = Blueprint("manage", __name__, template_folder="templates")

@manage_bp.route('/delete/<int:habit_id>', methods=['GET', 'POST'])
def delete_habit(habit_id):
    """
    Permite al usuario confirmar y eliminar un hábito.
    """
    if request.method == 'POST':
        # Eliminar el hábito
        Habit.delete(habit_id)
        flash("Habit deleted successfully!", "success")
        return redirect(url_for('explore.dashboard'))  # <-- ajusta según tu ruta principal

    # GET → mostrar la página de confirmación
    return render_template('manage/delete.html', habit_id=habit_id)
