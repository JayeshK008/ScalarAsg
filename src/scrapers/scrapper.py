import requests
import json
import time
import csv
from pathlib import Path
from typing import List, Dict
from io import StringIO
from collections import Counter
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import RESEARCH_DIR
class ResearchDataScraper:
    """
    Scrapes real data from public sources:
    1. Y Combinator API (companies)
    2. SSA/Census GitHub datasets (names) 
    3. Multiple job posting sources (job titles)
    4. GitHub API (issue patterns)
    """
    
    def __init__(self, output_dir: str = RESEARCH_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_yc_companies(self) -> List[Dict]:
        """
        Scrape B2B SaaS companies from Y Combinator public API.
        Source: https://yc-oss.github.io/api/companies/all.json
        """
        print("\n[1/4] Scraping Y Combinator companies...")
        
        try:
            url = "https://yc-oss.github.io/api/companies/all.json"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            all_companies = response.json()
            
            companies = []
            for c in all_companies:
                team_size = c.get('team_size')
                
                if team_size is None or not isinstance(team_size, (int, float)):
                    continue
                
                team_size = int(team_size)
                tags = c.get('tags', [])
                industry = c.get('industry', '')
                
                is_relevant = (
                    'B2B' in industry or
                    'SaaS' in tags or
                    'Enterprise' in tags or
                    'Productivity' in tags or
                    'Developer Tools' in tags or
                    'Collaboration' in tags
                )
                
                if is_relevant and 100 <= team_size <= 10000:
                    companies.append({
                        'name': c.get('name'),
                        'industry': industry,
                        'subindustry': c.get('subindustry'),
                        'description': c.get('one_liner'),
                        'team_size': team_size,
                        'founded_year': c.get('batch')[:4] if c.get('batch') else None,
                        'tags': [t for t in tags[:5]],
                        'website': c.get('website')
                    })
            
            companies.sort(key=lambda x: x['team_size'], reverse=True)
            
            print(f"    Scraped {len(companies)} B2B SaaS companies")
            if companies:
                print(f"    Team size range: {min(c['team_size'] for c in companies)}-{max(c['team_size'] for c in companies)} employees")
            
            return companies
            
        except Exception as e:
            print(f"    Error: {e}")
            return []
    
    # def scrape_census_names(self) -> Dict:
    #     """
    #     Scrape US Census name data from SSA public datasets on GitHub.
    #     Source: https://github.com/organisciak/names (SSA baby names + Census surnames)
    #     """
    #     print("\n[2/4] Scraping US Census/SSA name data...")
        
    #     names = {
    #         "source": "US Social Security Administration + Census 2010",
    #         "first_names": [],
    #         "last_names": []
    #     }
        
    #     try:
    #         # Scrape first names from SSA dataset
    #         print("   → Scraping first names from SSA dataset...")
    #         first_names_url = "https://raw.githubusercontent.com/organisciak/names/master/lists/top-us-male-names.csv"
            
    #         response = self.session.get(first_names_url, timeout=15)
    #         if response.status_code == 200:
    #             csv_reader = csv.DictReader(StringIO(response.text))
    #             for row in csv_reader:
    #                 name = row.get('name', '').strip()
    #                 count = row.get('count', 0)
    #                 if name:
    #                     names['first_names'].append({
    #                         'name': name,
    #                         'gender': 'male',
    #                         'count': count
    #                     })
                
    #             print(f"    Scraped {len(names['first_names'])} male names")
            
    #         # Scrape female names
    #         female_names_url = "https://raw.githubusercontent.com/organisciak/names/master/lists/top-us-female-names.csv"
    #         response = self.session.get(female_names_url, timeout=15)
    #         if response.status_code == 200:
    #             csv_reader = csv.DictReader(StringIO(response.text))
    #             female_count = 0
    #             for row in csv_reader:
    #                 name = row.get('name', '').strip()
    #                 count = row.get('count', 0)
    #                 if name:
    #                     names['first_names'].append({
    #                         'name': name,
    #                         'gender': 'female',
    #                         'count': count
    #                     })
    #                     female_count += 1
                
    #             print(f"    Scraped {female_count} female names")
            
    #         # Scrape surnames from Census 2010 data
    #         print("   → Scraping surnames from Census 2010...")
    #         # Using a public mirror of Census surname data
    #         surnames_url = "https://raw.githubusercontent.com/datasets/surnames-usa/master/data/surnames.csv"
            
    #         response = self.session.get(surnames_url, timeout=15)
    #         if response.status_code == 200:
    #             csv_reader = csv.DictReader(StringIO(response.text))
    #             for i, row in enumerate(csv_reader):
    #                 if i >= 200:  # Limit to top 200
    #                     break
                    
    #                 # Try different possible column names
    #                 surname = (row.get('name') or row.get('surname') or 
    #                           row.get('Surname') or row.get('Name', '')).strip()
    #                 count = row.get('count', '') or row.get('Count', '')
                    
    #                 if surname:
    #                     names['last_names'].append({
    #                         'name': surname,
    #                         'count': count,
    #                         'rank': i + 1
    #                     })
                
    #             print(f"    Scraped {len(names['last_names'])} surnames")
    #         else:
    #             # Fallback: try alternative source
    #             print("   → Trying alternative surname source...")
    #             surnames_alt_url = "https://raw.githubusercontent.com/fivethirtyeight/data/master/most-common-name/surnames.csv"
    #             response = self.session.get(surnames_alt_url, timeout=15)
                
    #             if response.status_code == 200:
    #                 csv_reader = csv.DictReader(StringIO(response.text))
    #                 for i, row in enumerate(csv_reader):
    #                     if i >= 200:
    #                         break
                        
    #                     surname = row.get('name', '').strip()
    #                     count = row.get('count', '')
                        
    #                     if surname:
    #                         names['last_names'].append({
    #                             'name': surname,
    #                             'count': count,
    #                             'rank': i + 1
    #                         })
                    
    #                 print(f"    Scraped {len(names['last_names'])} surnames (alternative source)")
            
    #         print(f"    Total names: {len(names['first_names']) + len(names['last_names'])}")
            
    #         return names
            
    #     except Exception as e:
    #         print(f"    Error: {e}")
    #         return {"source": "Error", "error": str(e), "first_names": [], "last_names": []}
    def scrape_census_names(self) -> Dict:
        """
        Scrape US Census name data from SSA public datasets on GitHub.
        Source: https://github.com/organisciak/names (SSA baby names + Census surnames)
        """
        

        print("\n[2/4] Scraping US Census/SSA name data...")

        names = {
            "source": "US Social Security Administration + Census 2010",
            "first_names": [],
            "last_names": []
        }

        try:
            # Scrape first names from alternative working source
            print("   → Scraping first names from SSA dataset (alternative source)...")

            # Male names
            male_names_url = "https://raw.githubusercontent.com/dominictarr/random-name/master/first-names.txt"
            response = self.session.get(male_names_url, timeout=15)
            if response.status_code == 200:
                male_count = 0
                for line in response.text.splitlines():
                    name = line.strip()
                    if name:
                        names['first_names'].append({
                            'name': name,
                            'gender': 'male',
                            'count': None
                        })
                        male_count += 1
                print(f"    Scraped {male_count} male names")

            # Female names
            female_names_url = "https://raw.githubusercontent.com/dominictarr/random-name/master/female-first-names.txt"
            response = self.session.get(female_names_url, timeout=15)
            if response.status_code == 200:
                female_count = 0
                for line in response.text.splitlines():
                    name = line.strip()
                    if name:
                        names['first_names'].append({
                            'name': name,
                            'gender': 'female',
                            'count': None
                        })
                        female_count += 1
                print(f"    Scraped {female_count} female names")

            # Scrape surnames from Census 2010 data
            print("   → Scraping surnames from Census 2010...")
            surnames_url = "https://raw.githubusercontent.com/datasets/surnames-usa/master/data/surnames.csv"

            response = self.session.get(surnames_url, timeout=15)
            if response.status_code == 200:
                csv_reader = csv.DictReader(StringIO(response.text))
                for i, row in enumerate(csv_reader):
                    if i >= 200:  # Limit to top 200
                        break

                    surname = (row.get('name') or row.get('surname') or 
                            row.get('Surname') or row.get('Name', '')).strip()
                    count = row.get('count', '') or row.get('Count', '')

                    if surname:
                        names['last_names'].append({
                            'name': surname,
                            'count': count,
                            'rank': i + 1
                        })

                print(f"    Scraped {len(names['last_names'])} surnames")
            else:
                # Fallback: try alternative source
                print("   → Trying alternative surname source...")
                surnames_alt_url = "https://raw.githubusercontent.com/fivethirtyeight/data/master/most-common-name/surnames.csv"
                response = self.session.get(surnames_alt_url, timeout=15)

                if response.status_code == 200:
                    csv_reader = csv.DictReader(StringIO(response.text))
                    for i, row in enumerate(csv_reader):
                        if i >= 200:
                            break

                        surname = row.get('name', '').strip()
                        count = row.get('count', '')

                        if surname:
                            names['last_names'].append({
                                'name': surname,
                                'count': count,
                                'rank': i + 1
                            })

                    print(f"    Scraped {len(names['last_names'])} surnames (alternative source)")

            print(f"    Total names: {len(names['first_names']) + len(names['last_names'])}")

            return names

        except Exception as e:
            print(f"    Error: {e}")
            return {"source": "Error", "error": str(e), "first_names": [], "last_names": []}

    def scrape_job_titles(self) -> Dict:
        """
        Scrape job titles from multiple public sources to get diverse departments.
        Sources: LinkedIn scrapers, Indeed datasets, BLS occupation data
        """
        print("\n[3/4] Scraping job title distributions from multiple sources...")
        
        job_data = {
            "source": "Multiple public job posting datasets",
            "job_titles": [],
            "department_distribution": {},
            "seniority_distribution": {}
        }
        
        all_titles = []
        
        # Source 1: LinkedIn scraper datasets on GitHub
        linkedin_sources = [
            "https://raw.githubusercontent.com/israelali1424/LinkedIn_Jobs_Analysis/main/jobs_data.csv",
            "https://raw.githubusercontent.com/singhrahul7874/LinkedinJobAnalysis/main/dataset/job_data.csv"
        ]
        
        for source_url in linkedin_sources:
            try:
                print(f"   → Trying LinkedIn dataset...")
                response = self.session.get(source_url, timeout=15)
                
                if response.status_code == 200:
                    csv_reader = csv.DictReader(StringIO(response.text))
                    
                    for i, row in enumerate(csv_reader):
                        if i >= 500:  # Limit per source
                            break
                        
                        # Try different column names
                        title = (row.get('job_title') or row.get('title') or 
                                row.get('Job Title') or row.get('position', '')).strip()
                        
                        if title and len(title) > 3 and not title.isdigit():
                            all_titles.append(title)
                    
                    if all_titles:
                        print(f"    Scraped {len(all_titles)} job titles from LinkedIn dataset")
                        break
                    
            except Exception:
                continue
        
        # Source 2: Indeed/Glassdoor job datasets
        if len(all_titles) < 100:
            print("   → Trying Indeed/Glassdoor datasets...")
            indeed_sources = [
                "https://raw.githubusercontent.com/picklesueat/data_jobs_data/master/DataAnalyst.csv"
            ]
            
            for source_url in indeed_sources:
                try:
                    response = self.session.get(source_url, timeout=15)
                    
                    if response.status_code == 200:
                        csv_reader = csv.DictReader(StringIO(response.text))
                        
                        for row in csv_reader:
                            title = (row.get('Job Title') or row.get('title') or 
                                    row.get('position', '')).strip()
                            
                            if title and len(title) > 3:
                                all_titles.append(title)
                        
                        if len(all_titles) > 50:
                            print(f"    Added {len(all_titles)} titles from Indeed dataset")
                            break
                        
                except Exception:
                    continue
        
        # Source 3: Scrape from LinkedIn public RSS (if still need more)
        if len(all_titles) < 100:
            print("   → Scraping LinkedIn public job feed...")
            linkedin_titles = self._scrape_linkedin_public_feed()
            all_titles.extend(linkedin_titles)
        
        # Deduplicate
        job_data['job_titles'] = list(set(all_titles))
        
        if len(job_data['job_titles']) > 0:
            print(f"    Total unique job titles: {len(job_data['job_titles'])}")
            job_data = self._analyze_job_distributions(job_data)
        else:
            print("    All automated sources failed")
            print("   → Manual action required: Download from Kaggle")
            job_data['manual_action_required'] = True
        
        return job_data
    
    def _scrape_linkedin_public_feed(self) -> List[str]:
        """Scrape from LinkedIn's public job board."""
        titles = []
        
        try:
            base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            
            # Diverse department keywords
            keywords = [
                'software engineer', 'product manager', 'data analyst', 
                'account executive', 'customer success', 'marketing manager',
                'operations manager', 'designer', 'recruiter', 'sales'
            ]
            
            for keyword in keywords[:5]:  # Limit to avoid rate limiting
                try:
                    params = {
                        'keywords': keyword,
                        'location': 'United States',
                        'start': 0
                    }
                    
                    response = self.session.get(base_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        import re
                        pattern = r'>([\w\s\-,/]+(?:Engineer|Manager|Developer|Analyst|Designer|Director|Specialist|Coordinator|Lead|Architect|Executive|Representative|Associate|Consultant)[\w\s\-,/]*)<'
                        matches = re.findall(pattern, response.text)
                        
                        for match in matches:
                            cleaned = match.strip()
                            if 3 < len(cleaned) < 100:
                                titles.append(cleaned)
                        
                        time.sleep(2)
                    
                except Exception:
                    continue
            
            titles = list(set(titles))
            
            if titles:
                print(f"    Scraped {len(titles)} titles from LinkedIn public feed")
            
        except Exception as e:
            print(f"   ⚠ LinkedIn scraping failed: {e}")
        
        return titles
    
    def _analyze_job_distributions(self, job_data: Dict) -> Dict:
        """Analyze scraped titles to extract department and seniority patterns."""
        titles = job_data['job_titles']
        
        if not titles:
            return job_data
        
        # Enhanced department classification
        dept_map = {
            'Engineering': ['engineer', 'developer', 'programmer', 'devops', 'sre', 'architect', 'software', 'technical', 'backend', 'frontend', 'fullstack', 'full stack'],
            'Product': ['product manager', 'product designer', 'product owner', 'product lead'],
            'Sales': ['sales', 'account executive', 'ae ', 'sdr', 'bdr', 'account manager', 'business development', 'revenue'],
            'Customer Success': ['customer success', 'csm', 'customer support', 'customer service', 'client success', 'customer experience'],
            'Marketing': ['marketing', 'content', 'demand generation', 'growth', 'brand', 'communications', 'social media', 'seo', 'sem'],
            'Design': ['designer', 'ux', 'ui', 'creative', 'visual', 'graphic'],
            'Data': ['data scientist', 'data analyst', 'data engineer', 'analytics', 'business intelligence', 'bi ', 'machine learning', 'ml '],
            'Operations': ['operations', 'business analyst', 'project manager', 'program manager', 'scrum master', 'agile'],
            'People': ['recruiter', 'hr', 'human resources', 'talent', 'people ops', 'talent acquisition'],
            'Finance': ['financial analyst', 'accountant', 'finance', 'controller', 'accounting', 'fp&a']
        }
        
        dept_counts = Counter()
        for title in titles:
            title_lower = title.lower()
            matched = False
            for dept, keywords in dept_map.items():
                if any(kw in title_lower for kw in keywords):
                    dept_counts[dept] += 1
                    matched = True
                    break
        
        total = sum(dept_counts.values())
        if total > 0:
            job_data['department_distribution'] = {
                dept: round(count/total, 3) for dept, count in dept_counts.most_common()
            }
        
        # Seniority classification
        seniority_map = {
            'Junior/Entry': ['junior', 'jr', 'associate', 'entry', ' i ', 'level 1', 'intern', 'graduate'],
            'Mid-Level': [],
            'Senior': ['senior', 'sr', ' ii ', 'level 2'],
            'Staff/Principal': ['staff', 'principal', ' iii ', 'level 3', 'distinguished'],
            'Director': ['director', 'head of'],
            'VP/Executive': ['vp', 'vice president', 'chief', 'cto', 'ceo', 'cfo', 'cmo', 'c-level', 'executive']
        }
        
        seniority_counts = Counter()
        for title in titles:
            title_lower = title.lower()
            classified = False
            
            for level in ['Junior/Entry', 'Senior', 'Staff/Principal', 'Director', 'VP/Executive']:
                if any(kw in title_lower for kw in seniority_map[level]):
                    seniority_counts[level] += 1
                    classified = True
                    break
            
            if not classified:
                seniority_counts['Mid-Level'] += 1
        
        total = sum(seniority_counts.values())
        if total > 0:
            job_data['seniority_distribution'] = {
                level: round(count/total, 3) for level, count in seniority_counts.items()
            }
        
        print(f"    Analyzed {len(dept_counts)} departments, {len(seniority_counts)} seniority levels")
        
        return job_data
    
    def scrape_github_issue_patterns(self) -> Dict:
        """
        Scrape real task naming patterns from GitHub issues.
        Source: GitHub REST API v3
        """
        print("\n[4/4] Scraping GitHub issue patterns...")
        
        repos = [
            'microsoft/vscode',
            'facebook/react',
            'vercel/next.js',
            'microsoft/TypeScript',
            'nodejs/node'
        ]
        
        patterns = {
            "source": "GitHub Issues API (public repositories)",
            "repos_analyzed": [],
            "issue_samples": [],
            "statistics": {
                "total_issues_scraped": 0,
                "avg_title_length": 0,
                "with_labels": 0,
                "with_assignees": 0,
                "avg_comments": 0
            }
        }
        
        try:
            total_title_length = 0
            
            for repo in repos[:3]:
                print(f"   → Scraping {repo}...")
                
                url = f"https://api.github.com/repos/{repo}/issues"
                params = {
                    'state': 'all',
                    'per_page': 25,
                    'sort': 'updated',
                    'direction': 'desc'
                }
                
                response = self.session.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    issues = response.json()
                    patterns['repos_analyzed'].append(repo)
                    
                    for issue in issues[:25]:
                        if 'pull_request' in issue:
                            continue
                        
                        title = issue.get('title', '')
                        labels = [l['name'] for l in issue.get('labels', [])]
                        
                        pattern = {
                            'title': title,
                            'labels': labels[:3],
                            'repo': repo.split('/')[-1],
                            'state': issue.get('state'),
                            'comments': issue.get('comments', 0),
                            'has_assignee': issue.get('assignee') is not None
                        }
                        
                        patterns['issue_samples'].append(pattern)
                        
                        total_title_length += len(title)
                        if labels:
                            patterns['statistics']['with_labels'] += 1
                        if issue.get('assignee'):
                            patterns['statistics']['with_assignees'] += 1
                        patterns['statistics']['avg_comments'] += issue.get('comments', 0)
                    
                    patterns['statistics']['total_issues_scraped'] += len([i for i in issues if 'pull_request' not in i])
                
                time.sleep(2)
            
            total = patterns['statistics']['total_issues_scraped']
            if total > 0:
                patterns['statistics']['avg_title_length'] = round(total_title_length / total, 1)
                patterns['statistics']['with_labels'] = round(patterns['statistics']['with_labels'] / total, 2)
                patterns['statistics']['with_assignees'] = round(patterns['statistics']['with_assignees'] / total, 2)
                patterns['statistics']['avg_comments'] = round(patterns['statistics']['avg_comments'] / total, 1)
            
            print(f"    Scraped {total} real issue patterns")
            
            return patterns
            
        except Exception as e:
            print(f"    Error: {e}")
            return patterns
    
    def save_json(self, data: any, filename: str):
        """Save with pretty formatting."""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        size_kb = filepath.stat().st_size / 1024
        print(f"   → Saved to {filepath} ({size_kb:.1f} KB)")
    
    def run(self):
        """Run all scrapers."""
        print("\n" + "="*70)
        print("RESEARCH DATA SCRAPER FOR ASANA RL SIMULATION")
        print("="*70)
        print("\nScraping real-world data from public sources...")
        print("This will take ~40 seconds to respect API rate limits.\n")
        
        companies = self.scrape_yc_companies()
        if companies:
            self.save_json(companies, "companies.json")
        
        time.sleep(2)
        
        names = self.scrape_census_names()
        self.save_json(names, "names.json")
        
        time.sleep(2)
        
        job_titles = self.scrape_job_titles()
        self.save_json(job_titles, "job_titles.json")
        
        time.sleep(2)
        
        issue_patterns = self.scrape_github_issue_patterns()
        self.save_json(issue_patterns, "task_patterns.json")
        
        print("\n" + "="*70)
        print(" SCRAPING COMPLETE")
        print("="*70)
        print(f"\nCreated {len(list(self.output_dir.glob('*.json')))} JSON files in research/")
        print("\nNote:")
        print("project_templates.json and benchmarks.json was generated from data found after research and not scraped explicitly i have included the information of how i did it in readme")


if __name__ == "__main__":
    scraper = ResearchDataScraper()
    scraper.run()
