// ============================================================
// DIFF CLEAN LEADERBOARD UPGRADE
// ============================================================

const {
EmbedBuilder,
ActionRowBuilder,
ButtonBuilder,
ButtonStyle,
} = require('discord.js');
const fs = require('fs');

// ===============================
// CONFIG
// ===============================

const CONFIG = {
leaderboardChannelId: 'PUT_LEADERBOARD_CHANNEL_ID_HERE',
crewHubChannelId: 'PUT_CREW_HUB_CHANNEL_ID_HERE',
notifyRoleId: 'PUT_NOTIFY_ROLE_ID_HERE',
};

const DATA_FILE = './data/diff_data.json';

// ===============================
// DATA
// ===============================

function loadData() {
if (!fs.existsSync(DATA_FILE)) {
fs.writeFileSync(DATA_FILE, JSON.stringify({ users: {} }, null, 2));
}
return JSON.parse(fs.readFileSync(DATA_FILE));
}

function saveData(data) {
fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
}

// ===============================
// SORT USERS
// ===============================

function getUsers() {
const data = loadData();

return Object.entries(data.users).map(([id, u]) => ({
id,
attendance: u.attendance || 0,
last: u.lastAttendance || 0,
improvement: (u.attendance || 0) - (u.lastAttendance || 0),
photos: u.photos || 0
})).sort((a,b)=>b.attendance-a.attendance);
}

// ===============================
// LEADERBOARD
// ===============================

function leaderboardEmbed() {
const users = getUsers();
const top3 = users.slice(0,3);
const rest = users.slice(3,10);

const top = [
top3[0] && `🥇 <@${top3[0].id}> — ${top3[0].attendance}`,
top3[1] && `🥈 <@${top3[1].id}> — ${top3[1].attendance}`,
top3[2] && `🥉 <@${top3[2].id}> — ${top3[2].attendance}`
].filter(Boolean).join("\n");

const others = rest.map((u,i)=>
`📌 ${i+4}. <@${u.id}> — ${u.attendance}`
).join("\n");

const improved = users.sort((a,b)=>b.improvement-a.improvement)[0];

return new EmbedBuilder()
.setTitle("🏆 DIFF Leaderboard")
.setDescription(
`${top}\n━━━━━━━━━━━━\n${others}\n━━━━━━━━━━━━\n📈 Most Improved: <@${improved?.id}> (+${improved?.improvement || 0})`
);
}

// ===============================
// CREW HUB
// ===============================

function hubEmbed() {
const users = getUsers();

return new EmbedBuilder()
.setTitle("📊 Crew Hub")
.setDescription(
`Tracked: ${users.length}\n`+
`Active: ${users.filter(u=>u.attendance>0).length}\n`+
`Total Attendance: ${users.reduce((a,b)=>a+b.attendance,0)}`
);
}

// ===============================
// PANEL SYSTEM (AUTO EDIT)
// ===============================

async function updatePanel(client, channelId, type) {
const ch = await client.channels.fetch(channelId);
const msgs = await ch.messages.fetch({limit:10});

const existing = msgs.find(m => m.author.id === client.user.id);

const embed = type === "lb" ? leaderboardEmbed() : hubEmbed();
const id = type === "lb" ? "refresh_lb" : "refresh_hub";

const row = new ActionRowBuilder().addComponents(
new ButtonBuilder()
.setCustomId(id)
.setLabel("Refresh")
.setStyle(ButtonStyle.Secondary)
);

if (existing) {
await existing.edit({embeds:[embed], components:[row]});
} else {
await ch.send({embeds:[embed], components:[row]});
}
}

// ===============================
// READY
// ===============================

module.exports = (client) => {

client.once("ready", () => {
updatePanel(client, CONFIG.leaderboardChannelId, "lb");
updatePanel(client, CONFIG.crewHubChannelId, "hub");

setInterval(()=>{
updatePanel(client, CONFIG.leaderboardChannelId, "lb");
updatePanel(client, CONFIG.crewHubChannelId, "hub");
}, 1000*60*60*24*7);
});

// ===============================
// BUTTONS
// ===============================

client.on("interactionCreate", async (i) => {

if (!i.isButton()) return;

if (i.customId === "refresh_lb") {
updatePanel(client, CONFIG.leaderboardChannelId, "lb");
return i.reply({content:"Updated", ephemeral:true});
}

if (i.customId === "refresh_hub") {
updatePanel(client, CONFIG.crewHubChannelId, "hub");
return i.reply({content:"Updated", ephemeral:true});
}

});

};
