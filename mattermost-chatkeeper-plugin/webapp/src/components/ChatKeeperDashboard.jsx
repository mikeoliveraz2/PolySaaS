import React, { useState, useEffect } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area
} from 'recharts';
import { format, subDays, startOfWeek, endOfWeek } from 'date-fns';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

const ChatKeeperDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [analytics, setAnalytics] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exportFormat, setExportFormat] = useState('json');
  const [dateRange, setDateRange] = useState({
    start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd')
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [tags, setTags] = useState([]);
  const [backups, setBackups] = useState([]);
  const [sentiment, setSentiment] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    fetchTags();
    fetchBackups();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard stats
      const statsResponse = await fetch('/api/v1/dashboard');
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      // Fetch analytics
      const analyticsResponse = await fetch('/api/v1/analytics');
      if (analyticsResponse.ok) {
        const analyticsData = await analyticsResponse.json();
        setAnalytics(analyticsData);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTags = async () => {
    try {
      const response = await fetch('/api/v1/tags');
      if (response.ok) {
        const data = await response.json();
        setTags(data);
      }
    } catch (error) {
      console.error('Failed to fetch tags:', error);
    }
  };

  const fetchBackups = async () => {
    try {
      const response = await fetch('/api/v1/backups');
      if (response.ok) {
        const data = await response.json();
        setBackups(data);
      }
    } catch (error) {
      console.error('Failed to fetch backups:', error);
    }
  };

  const handleExport = async () => {
    try {
      const response = await fetch('/api/v1/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          format: exportFormat,
          start_date: new Date(dateRange.start).toISOString(),
          end_date: new Date(dateRange.end).toISOString()
        })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chatkeeper_export_${format(new Date(), 'yyyy-MM-dd')}.${exportFormat === 'json' ? 'json' : exportFormat === 'csv' ? 'csv' : 'pdf'}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    }
  };

  const handleBackup = async () => {
    try {
      const response = await fetch('/api/v1/backup', { method: 'POST' });
      if (response.ok) {
        const data = await response.json();
        alert('Backup started successfully!');
        fetchBackups();
      }
    } catch (error) {
      console.error('Backup failed:', error);
      alert('Backup failed. Please try again.');
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    try {
      const response = await fetch(`/api/v1/search?q=${encodeURIComponent(searchQuery)}`);
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data);
      }
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const handleTagAdd = async (channelId, tag) => {
    try {
      await fetch('/api/v1/tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_id: channelId, tag })
      });
      fetchTags();
    } catch (error) {
      console.error('Failed to add tag:', error);
    }
  };

  // Prepare chart data
  const hourlyActivityData = analytics?.most_active_times 
    ? Object.entries(analytics.most_active_times).map(([hour, count]) => ({
        hour: `${hour}:00`,
        messages: count
      })).sort((a, b) => parseInt(a.hour) - parseInt(b.hour))
    : [];

  const channelActivityData = analytics?.top_channels?.map(ch => ({
    name: ch.channel_name || 'Unknown',
    messages: ch.post_count
  })) || [];

  const sentimentData = sentiment ? [
    { name: 'Positive', value: sentiment.positive || 0 },
    { name: 'Neutral', value: sentiment.neutral || 0 },
    { name: 'Negative', value: sentiment.negative || 0 }
  ] : [];

  const renderOverview = () => (
    <div className="dashboard-grid">
      <div className="stat-cards">
        <div className="stat-card">
          <div className="stat-value">{stats?.total_channels || 0}</div>
          <div className="stat-label">Active Channels</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.recent_posts_7d || 0}</div>
          <div className="stat-label">Messages (7 days)</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{analytics?.active_contacts || 0}</div>
          <div className="stat-label">Active Contacts</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{backups.length}</div>
          <div className="stat-label">Backups</div>
        </div>
      </div>

      <div className="charts-row">
        <div className="chart-container">
          <h3>Hourly Activity</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={hourlyActivityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey="messages" stroke="#8884d8" fill="#8884d8" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Top Channels</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={channelActivityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="messages" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );

  const renderExport = () => (
    <div className="export-section">
      <h2>Export Conversations</h2>
      
      <div className="export-form">
        <div className="form-group">
          <label>Date Range</label>
          <div className="date-inputs">
            <input 
              type="date" 
              value={dateRange.start}
              onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
            />
            <span>to</span>
            <input 
              type="date" 
              value={dateRange.end}
              onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
            />
          </div>
        </div>

        <div className="form-group">
          <label>Export Format</label>
          <select value={exportFormat} onChange={(e) => setExportFormat(e.target.value)}>
            <option value="json">JSON (Full Data)</option>
            <option value="csv">CSV (Spreadsheet)</option>
            <option value="pdf">PDF (Readable)</option>
          </select>
        </div>

        <div className="form-group">
          <label>Options</label>
          <div className="checkbox-group">
            <label>
              <input type="checkbox" checked readOnly /> Include message metadata
            </label>
            <label>
              <input type="checkbox" /> Include file attachments
            </label>
            <label>
              <input type="checkbox" /> Include reactions
            </label>
          </div>
        </div>

        <button className="btn-primary" onClick={handleExport}>
          <i className="fa fa-download"></i> Export Now
        </button>
      </div>
    </div>
  );

  const renderBackup = () => (
    <div className="backup-section">
      <h2>Cloud Backup</h2>
      
      <div className="backup-info">
        <p>
          <i className="fa fa-cloud"></i>
          Your conversations are automatically backed up to secure cloud storage.
        </p>
      </div>

      <div className="backup-actions">
        <button className="btn-primary" onClick={handleBackup}>
          <i className="fa fa-cloud-upload"></i> Backup Now
        </button>
      </div>

      <h3>Backup History</h3>
      <div className="backup-list">
        {backups.length === 0 ? (
          <p className="empty-state">No backups yet. Click "Backup Now" to create your first backup.</p>
        ) : (
          backups.map(backup => (
            <div key={backup.id} className="backup-item">
              <div className="backup-info">
                <span className="backup-date">{format(new Date(backup.created_at), 'MMM dd, yyyy HH:mm')}</span>
                <span className="backup-size">{(backup.size_bytes / 1024 / 1024).toFixed(2)} MB</span>
                <span className="backup-posts">{backup.post_count} posts</span>
              </div>
              <div className="backup-actions">
                <button className="btn-small">Download</button>
                <button className="btn-small btn-danger">Delete</button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );

  const renderSearch = () => (
    <div className="search-section">
      <h2>Search Conversations</h2>
      
      <div className="search-box">
        <input
          type="text"
          placeholder="Search for messages, keywords, or phrases..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button onClick={handleSearch}>
          <i className="fa fa-search"></i> Search
        </button>
      </div>

      <div className="search-filters">
        <label>Filter by:</label>
        <select>
          <option>All Time</option>
          <option>Last 7 days</option>
          <option>Last 30 days</option>
          <option>Last 90 days</option>
        </select>
        <select>
          <option>All Channels</option>
          <option>Current Channel</option>
          <option>Direct Messages</option>
        </select>
      </div>

      <div className="search-results">
        {searchResults.length === 0 ? (
          searchQuery ? (
            <p className="empty-state">No results found for "{searchQuery}"</p>
          ) : (
            <p className="empty-state">Enter a search query to find conversations</p>
          )
        ) : (
          searchResults.map(result => (
            <div key={result.id} className="search-result">
              <div className="result-header">
                <span className="result-user">{result.username}</span>
                <span className="result-time">{format(new Date(result.create_at), 'MMM dd, HH:mm')}</span>
              </div>
              <div className="result-message">{result.message}</div>
              <div className="result-channel">in #{result.channel_name}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );

  const renderTags = () => (
    <div className="tags-section">
      <h2>Conversation Categories</h2>
      
      <div className="tags-grid">
        {tags.length === 0 ? (
          <p className="empty-state">No categories yet. Use /chatkeeper tag &lt;category&gt; in any channel.</p>
        ) : (
          tags.map((tag, index) => (
            <div key={index} className="tag-card">
              <div className="tag-name">{tag.name}</div>
              <div className="tag-count">{tag.count} channels</div>
              <div className="tag-channels">
                {tag.channels?.map(ch => (
                  <span key={ch.id} className="tag-channel">{ch.name}</span>
                ))}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="tag-instructions">
        <h3>How to categorize conversations:</h3>
        <code>/chatkeeper tag work</code> - Tag current channel as "work"
        <code>/chatkeeper tag personal</code> - Tag as "personal"
        <code>/chatkeeper tag project-alpha</code> - Create custom category
      </div>
    </div>
  );

  const renderAnalytics = () => (
    <div className="analytics-section">
      <h2>Detailed Analytics</h2>
      
      <div className="analytics-grid">
        <div className="analytics-card">
          <h3>Conversation Volume</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={hourlyActivityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="messages" stroke="#8884d8" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {sentiment && (
          <div className="analytics-card">
            <h3>Sentiment Distribution</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  fill="#8884d8"
                  paddingAngle={5}
                  dataKey="value"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="analytics-table">
        <h3>Channel Activity Summary</h3>
        <table>
          <thead>
            <tr>
              <th>Channel</th>
              <th>Messages</th>
              <th>Last Active</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {analytics?.top_channels?.map(channel => (
              <tr key={channel.channel_id}>
                <td>{channel.channel_name}</td>
                <td>{channel.post_count}</td>
                <td>{format(new Date(channel.last_post_at), 'MMM dd, yyyy')}</td>
                <td>
                  <button className="btn-small">Export</button>
                  <button className="btn-small">Analyze</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div className="chatkeeper-dashboard">
      <header className="dashboard-header">
        <h1><i className="fa fa-archive"></i> ChatKeeper</h1>
        <p>Conversation History, Backup & Analytics</p>
      </header>

      <nav className="dashboard-nav">
        <button 
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          <i className="fa fa-dashboard"></i> Overview
        </button>
        <button 
          className={activeTab === 'export' ? 'active' : ''}
          onClick={() => setActiveTab('export')}
        >
          <i className="fa fa-download"></i> Export
        </button>
        <button 
          className={activeTab === 'backup' ? 'active' : ''}
          onClick={() => setActiveTab('backup')}
        >
          <i className="fa fa-cloud"></i> Cloud Backup
        </button>
        <button 
          className={activeTab === 'search' ? 'active' : ''}
          onClick={() => setActiveTab('search')}
        >
          <i className="fa fa-search"></i> Search
        </button>
        <button 
          className={activeTab === 'tags' ? 'active' : ''}
          onClick={() => setActiveTab('tags')}
        >
          <i className="fa fa-tags"></i> Categories
        </button>
        <button 
          className={activeTab === 'analytics' ? 'active' : ''}
          onClick={() => setActiveTab('analytics')}
        >
          <i className="fa fa-bar-chart"></i> Analytics
        </button>
      </nav>

      <main className="dashboard-content">
        {loading ? (
          <div className="loading-state">
            <i className="fa fa-spinner fa-spin"></i>
            <p>Loading your conversation data...</p>
          </div>
        ) : (
          <>
            {activeTab === 'overview' && renderOverview()}
            {activeTab === 'export' && renderExport()}
            {activeTab === 'backup' && renderBackup()}
            {activeTab === 'search' && renderSearch()}
            {activeTab === 'tags' && renderTags()}
            {activeTab === 'analytics' && renderAnalytics()}
          </>
        )}
      </main>

      <footer className="dashboard-footer">
        <p>ChatKeeper v1.0.0 | PolySaaS Integration</p>
      </footer>
    </div>
  );
};

export default ChatKeeperDashboard;
