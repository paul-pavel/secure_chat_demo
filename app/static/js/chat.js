(function(){
  const groupsDiv = document.getElementById('groups');
  const activeUsersUl = document.getElementById('activeUsers');
  const messagesDiv = document.getElementById('messages');
  const createGroupForm = document.getElementById('createGroupForm');
  const groupNameInput = document.getElementById('groupName');
  const messageForm = document.getElementById('messageForm');
  const messageInput = document.getElementById('messageInput');
  let currentGroup = null;
  let ws = null;

  function api(url, opts={}){
    return fetch(url, opts).then(r => {
      if (!r.ok) throw new Error('HTTP '+r.status);
      return r.json();
    });
  }

  function renderGroups(list){
    groupsDiv.innerHTML = '';
    list.forEach(g => {
      const btn = document.createElement('button');
      btn.textContent = g.name;
      btn.className = 'ghost';
      btn.onclick = () => joinAndOpen(g.id);
      groupsDiv.appendChild(btn);
    });
  }

  function renderMessages(list){
    messagesDiv.innerHTML = '';
    list.forEach(m => {
      const div = document.createElement('div');
      div.className = 'msg';
      div.textContent = m.author+': '+m.content;
      messagesDiv.appendChild(div);
    });
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  function addIncoming(text){
    const div = document.createElement('div');
    try {
        const message = JSON.parse(text);
        div.className = 'msg';
        div.textContent = `${message.author}: ${message.content}`;
    } catch (e) {
        div.className = 'sys';
        div.textContent = text;
    }
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  function openWS(groupId){
    if (ws) ws.close();
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${proto}://${location.host}/ws/chat/${groupId}`);
    ws.onmessage = (e) => addIncoming(e.data);
    ws.onclose = () => {};
  }

  function joinAndOpen(groupId){
    api('/api/groups/join?group_id='+groupId, { method: 'POST' })
      .then(() => api('/api/messages?group_id='+groupId))
      .then(msgs => {
        currentGroup = groupId;
        renderMessages(msgs);
        openWS(groupId);
      })
      .catch(e => console.error(e));
  }

  createGroupForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = groupNameInput.value.trim();
    if (!name) return;
    api('/api/groups?name='+encodeURIComponent(name), { method: 'POST' })
      .then(g => loadGroups())
      .catch(e => alert('Failed: '+e.message));
  });

  messageForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const txt = messageInput.value.trim();
    if (!txt || !ws) return;
    ws.send(txt);
    messageInput.value = '';
  });

  function loadGroups(){
    api('/api/groups').then(renderGroups).catch(console.error);
  }
  function loadActiveUsers(){
    api('/api/users/active').then(list => {
      activeUsersUl.innerHTML='';
      list.forEach(u => {
        const li = document.createElement('li');
        li.textContent = u.username;
        activeUsersUl.appendChild(li);
      });
    }).catch(console.error);
  }

  loadGroups();
  loadActiveUsers();
  setInterval(loadActiveUsers, 4000);

  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
      themeToggle.addEventListener('click', () => {
          document.body.classList.toggle('dark-theme');
      });
  }

  const notificationWs = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`);

  notificationWs.onmessage = function(event) {
      const message = event.data;
      if (message.startsWith("new_group:")) {
          // A simple way to update the group list is to reload the page.
          window.location.reload();
      }
  };

})();
