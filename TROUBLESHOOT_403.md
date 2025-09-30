# Quick Flask App Troubleshooting Guide

## If you're getting HTTP 403 errors on email confirmation:

### 1. Check if Flask is Running
```bash
# Look for running Python processes
ps aux | grep python | grep app.py

# Or check if port 5000 is in use
lsof -i :5000
```

### 2. Start the Flask App
```bash
cd /Users/prathyet/Websites/InterSpark
python app.py
```

### 3. Check Environment Variables
Make sure your `.env` file exists and contains:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SITE_URL=http://localhost:5000
```

### 4. Test the Route Manually
```bash
# Test if the route is accessible
curl http://localhost:5000/auth/confirm

# Test with your specific token
curl "http://localhost:5000/auth/confirm?token=782077&type=signup"
```

### 5. Common Issues

**ModuleNotFoundError**: Install dependencies
```bash
pip install -r requirements.txt
```

**Port Already in Use**: Kill existing process or use different port
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or start on different port
export FLASK_RUN_PORT=5001
python app.py
```

**Supabase Connection**: Check your credentials in `.env`

### 6. Debug Mode
Add this to see detailed error messages:
```python
# In app.py, at the bottom:
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
```

### 7. Browser Issues
- Clear browser cache
- Try incognito/private mode
- Try different browser
- Check browser console for JavaScript errors