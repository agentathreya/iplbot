# 🏏 IPL Cricket Analytics Chatbot

An advanced cricket analytics chatbot that provides accurate IPL statistics using natural language queries. Built with Streamlit and powered by comprehensive IPL data from 2008-2025.

## 🚀 Features

- **Natural Language Queries**: Ask cricket questions in plain English
- **Advanced Analytics**: Player vs player matchups, phase analysis, top performers
- **Accurate Statistics**: Properly calculated batting averages, economy rates, strike rates
- **Complex Filtering**: Multi-dimensional filtering by overs, bowling type, seasons
- **Real-time Results**: Instant query processing and visualization

## 🎯 Example Queries

- `best batters in middle overs v spin min. 1000 runs order by average`
- `kohli runs in overs 7 to 10`
- `bowlers with the worst economy rate`
- `most sixes in death overs`
- `CSK vs MI head to head record`
- `Rashid Khan v LHB`

## 🏗️ Architecture

- **Frontend**: Streamlit web application
- **Backend**: PostgreSQL database with normalized cricket data
- **Query Engine**: AI-powered natural language to SQL conversion
- **Data**: 277K+ ball-by-ball records from IPL 2008-2025

## 🛠️ Local Development

1. **Clone the repository**
```bash
git clone https://github.com/agentathreya/iplbot.git
cd iplbot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. **Run the application**
```bash
streamlit run streamlit_correct_cricket.py
```

## 🌐 Deployment

### Heroku Deployment

1. **Create a Heroku app**
```bash
heroku create your-ipl-chatbot
```

2. **Set environment variables**
```bash
heroku config:set DATABASE_URL="your-postgresql-connection-string"
```

3. **Deploy**
```bash
git push heroku main
```

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `STREAMLIT_SERVER_PORT`: Port for Streamlit (default: 8501)
- `LOG_LEVEL`: Logging level (default: INFO)

## 📊 Database Schema

The application uses a normalized database schema with the following key tables:
- `ipl_data_complete`: Complete ball-by-ball data (277K+ records)
- `player_profiles`: Player information and statistics
- `team_profiles`: Team details and performance
- `match_results`: Match outcomes and summaries

## 🎨 Query Types Supported

1. **Basic Stats**: Individual player/team statistics
2. **Phase Analysis**: Powerplay, middle overs, death overs performance
3. **Matchups**: Player vs player, team vs team comparisons
4. **Top Performers**: Rankings and leaderboards
5. **Complex Filtering**: Multiple conditions with sorting

## 🧪 Testing

Run the test suite to verify query accuracy:
```bash
python test_correct_cricket.py
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🏏 Data Sources

- IPL ball-by-ball data (2008-2025)
- Player statistics and profiles
- Team performance metrics
- Match results and outcomes

## ⚡ Performance

- **Query Response Time**: < 0.2s average
- **Database Size**: 277K+ records
- **Success Rate**: 95%+ query accuracy
- **Supported Players**: 765+ players
- **Supported Teams**: 19 teams

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review example queries

---

Built with ❤️ for cricket analytics enthusiasts