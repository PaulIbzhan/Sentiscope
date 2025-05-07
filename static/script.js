(async () => {
  const feedEl = document.getElementById('feed');
  const chartCtx = document.getElementById('sentimentChart').getContext('2d');

  // Initial fetch of posts
  let posts = await fetch('/get_posts').then(r => r.json()).then(d => d.posts);

  // Initialize Chart.js pie chart
  const chart = new Chart(chartCtx, {
    type: 'pie',
    data: {
      labels: ['HP','P','MP','N','MN','Neg','HN','TMI','Lewd'],
      datasets: [{
        data: Array(9).fill(0),
        backgroundColor: ['#4caf50','#8bc34a','#c8e6c9','#ffeb3b','#ffe0b2','#f44336','#b71c1c','#ffca28','#ab47bc']
      }]
    }
  });

  // Helper to post a comment and alert on auto-delete
  async function postComment(i, text) {
    const res = await fetch('/add_comment', {
      method: 'POST',
      body: new URLSearchParams({ comment: text, postIndex: i })
    });
    const data = await res.json();
    if (data.message) alert(data.message);            // notify user
    posts = await fetch('/get_posts').then(r => r.json()).then(d => d.posts);
    render();
  }

  // Render posts + comments
  function render() {
    feedEl.innerHTML = '';
    posts.forEach((post, i) => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <h3>Post ${i+1}</h3>
        <img src="/static/${post.image}" alt="Post ${i+1}">
        <div class="comments" id="comments-${i}"></div>
        <div class="input-area">
          <input type="text" placeholder="Write a comment..." id="input-${i}">
          <button data-post="${i}">Post</button>
        </div>
      `;
      feedEl.append(card);

      const commentsEl = card.querySelector('.comments');
      post.comments.forEach((c, j) => {
        const div = document.createElement('div');
        const cls = c.sentiment.toLowerCase().replace(/ /g,'-');
        div.className = `comment ${cls}`;
        div.innerHTML = `
          <span>${c.text} <em>(${c.sentiment}, ${c.toxicity}%)</em></span>
          <button data-del-post="${i}" data-del-idx="${j}">🗑️</button>
        `;
        commentsEl.append(div);
      });
    });
    updateChart();
    bindEvents();
  }

  // Attach all event handlers
  function bindEvents() {
    // Posting comments
    document.querySelectorAll('.input-area button').forEach(btn => {
      btn.onclick = () => {
        const i = btn.dataset.post;
        const text = document.getElementById(`input-${i}`).value.trim();
        if (!text) return;
        postComment(i, text);
      };
    });

    // Deleting single comments
    document.querySelectorAll('[data-del-post]').forEach(btn => {
      btn.onclick = async () => {
        await fetch('/delete_comment', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({
            postIndex: +btn.dataset.delPost,
            commentIndex: +btn.dataset.delIdx
          })
        });
        posts = await fetch('/get_posts').then(r => r.json()).then(d => d.posts);
        render();
      };
    });

    // Applying auto-delete settings
    document.getElementById('applySettings').onclick = async () => {
      const settings = {};
      document.querySelectorAll('.auto-delete').forEach(cb => {
        settings[cb.value] = cb.checked;
      });
      await fetch('/update_auto_delete', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ settings })
      });
      posts = await fetch('/get_posts').then(r => r.json()).then(d => d.posts);
      render();
    };

    // Bulk delete by sentiment type
    document.querySelectorAll('.bulk-btn').forEach(btn => {
      btn.onclick = async () => {
        await fetch('/delete_all_by_type', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ commentType: btn.dataset.type })
        });
        posts = await fetch('/get_posts').then(r => r.json()).then(d => d.posts);
        render();
      };
    });

    // Export CSV
    document.getElementById('exportCsv').onclick = () => {
      window.location = '/export_comments';
    };

    // Export Excel
    document.getElementById('exportExcel').onclick = () => {
      window.location = '/export_excel';
    };
  }

  // Update the pie chart data
  async function updateChart() {
    const data = await fetch('/get_chart_data').then(r => r.json());
    chart.data.datasets[0].data = [
      data['Highly Positive'], data['Positive'], data['Mildly Positive'],
      data['Neutral'],       data['Mildly Negative'], data['Negative'],
      data['Highly Negative'], data['TMI'],           data['Lewd']
    ];
    chart.update();
  }

  // Initial render & periodic chart refresh
  render();
  setInterval(updateChart, 5000);
})();
