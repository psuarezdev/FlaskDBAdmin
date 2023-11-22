document.addEventListener('DOMContentLoaded', () => {
  const addRegisterForm = document.getElementById('addRegisterModal');
  const execQuery = document.getElementById('execQuery');
  const codeEditor = document.getElementById('code-editor');
  const resetSQL = document.getElementById('resetSQL');

  codeEditor.addEventListener('keydown', e => {
    if(e.key === 'Tab') {
      e.preventDefault();

      const start = codeEditor.selectionStart;
      const end = codeEditor.selectionEnd;

      codeEditor.value = codeEditor.value.substring(0, start) + '\t' + codeEditor.value.substring(end);
      codeEditor.selectionStart = codeEditor.selectionEnd = start + 1;
    }
  });

  resetSQL.addEventListener('click', () => {
    const result = confirm('¿Estás seguro de que quieres reiniciar el editor de SQL?');
    if(!result) return;

    const resultsTable = document.getElementById('resultsTable');

    codeEditor.value = '';
    resultsTable.querySelector('thead tr').innerHTML = '';
    resultsTable.querySelector('tbody').innerHTML = '';
  });

  execQuery.addEventListener('click', async() => {
    let isSelect = true;

    if(codeEditor.value.trim().length <= 0) return alert('No se puede ejecutar una consulta vacía');

    if(!codeEditor.value.toLowerCase().includes('select')) isSelect = false;

    if(codeEditor.value.toLowerCase().includes('delete') || codeEditor.value.toLowerCase().includes('update') || codeEditor.value.toLowerCase().includes('drop') || codeEditor.value.toLowerCase().includes('alter')) {
      const result = confirm('¿Estás seguro de que quieres ejecutar esta consulta?');
      if(!result) return;
    }

    const response = await fetch('/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `query=${codeEditor.value}`
    });

    if(!isSelect) return window.location.reload();

    const data = await response.json();

    if(Object.keys(data).includes('rows') && Object.keys(data).includes('fields')) {
      const resultsTable = document.getElementById('resultsTable');

      resultsTable.querySelector('thead tr').innerHTML = '';

      data.fields.forEach(field => {
        const th = document.createElement('th');
        th.textContent = field[0];

        resultsTable.querySelector('thead tr').appendChild(th);
      });

      resultsTable.querySelector('tbody').innerHTML = '';

      data.rows.forEach(row => {
        const tr = document.createElement('tr');

        row.forEach(value => {
          const td = document.createElement('td');
          td.textContent = value;

          tr.appendChild(td);
        });

        resultsTable.querySelector('tbody').appendChild(tr);
      });
    }
  });

  addRegisterForm.addEventListener('submit', e => {
    e.preventDefault();

    const table = e.target.table.value;

    const data = {};

    e.target.querySelectorAll('input[type=text]').forEach(input => data[input.name] = input.value);

    fetch('/insert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `table=${table}&data=${JSON.stringify(data)}`
    });

    window.location.reload();
  });

  document.querySelectorAll('#registersTable tbody tr').forEach(tr => {
    const deleteButton = tr.querySelector(`#delete_${tr.id}`).querySelector('button');
    const editButton = tr.querySelector(`#edit_${tr.id}`).querySelector('button');
  
    const table = tr.id.split('_')[0];
    const row_id = tr.id.split('_')[1];
  
    deleteButton.addEventListener('click', () => {
      const result = confirm('¿Estás seguro de que quieres eliminar este registro?');

      if(!result) return;

      fetch('/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `table=${table}&row_id=${row_id}`
      });
  
      tr.remove();
    });
  
    editButton.addEventListener('click', () => {
      const inputs = tr.querySelectorAll('input');
  
      inputs.forEach(input => input.disabled = false);
  
      if(editButton.textContent === 'Editar') {
        editButton.textContent = 'Guardar';
      } else {
        const data = {};
  
        inputs.forEach(input => data[input.name] = input.value);

        fetch('/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: `table=${table}&row_id=${row_id}&data=${JSON.stringify(data)}`
        });

        inputs.forEach(input => input.disabled = true);
        editButton.textContent = 'Editar';
      }
    });
  });
});