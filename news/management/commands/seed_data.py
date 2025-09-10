from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from categories.models import Category
from news.models import Article, Comment, Like, Bookmark, Tag
from django.utils import timezone
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with sample data"

    def handle(self, *args, **options):
        # create users
        self.stdout.write("Creating users...")

        # create editor
        editor, _ = User.objects.get_or_create(
            username="editor",
            defaults={
                "email": "editor@example.com",
                "first_name": "John",
                "last_name": "Editor",
                "role": "editor",
                "is_staff": True,
            },
        )
        editor.set_password("password")
        editor.save()

        # create journalists
        journalists = []
        for i in range(3):
            username = f"journalist{i+1}"
            journalist, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "first_name": f"Journalist{i+1}",
                    "last_name": "User",
                    "role": "journalist",
                },
            )
            journalist.set_password("password")
            journalist.save()
            journalists.append(journalist)

        # create readers
        readers = []
        for i in range(5):
            username = f"reader{i+1}"
            reader, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "first_name": f"Reader{i+1}",
                    "last_name": "User",
                    "role": "reader",
                },
            )
            reader.set_password("password")
            reader.save()
            readers.append(reader)

        # create categories
        self.stdout.write("Creating categories...")

        main_categories = [
            {"name": "Politics", "description": "Political news and analysis"},
            {"name": "Technology", "description": "Latest tech news and innovations"},
            {"name": "Sports", "description": "Sports news and updates"},
            {"name": "Entertainment", "description": "Entertainment industry news"},
            {"name": "Business", "description": "Business and finance news"},
            {"name": "Health", "description": "Health and wellness news"},
        ]

        categories = []
        for cat_data in main_categories:
            category, _ = Category.objects.get_or_create(
                name=cat_data["name"], defaults={"description": cat_data["description"]}
            )
            categories.append(category)

        # create subcategories
        subcategories = [
            {"name": "US Politics", "parent": "Politics"},
            {"name": "International Politics", "parent": "Politics"},
            {"name": "AI & Machine Learning", "parent": "Technology"},
            {"name": "Cybersecurity", "parent": "Technology"},
            {"name": "Football", "parent": "Sports"},
            {"name": "Basketball", "parent": "Sports"},
            {"name": "Movies", "parent": "Entertainment"},
            {"name": "Music", "parent": "Entertainment"},
            {"name": "Startups", "parent": "Business"},
            {"name": "Cryptocurrency", "parent": "Business"},
            {"name": "Mental Health", "parent": "Health"},
            {"name": "Fitness", "parent": "Health"},
        ]

        for sub_data in subcategories:
            parent = Category.objects.get(name=sub_data["parent"])
            Category.objects.get_or_create(
                name=sub_data["name"], defaults={"parent": parent}
            )

        # tag pool for taggit
        self.stdout.write("Preparing tag pool...")

        tag_names = [
            'Breaking News', 'Analysis', 'Opinion', 'Interview', 'Investigation',
            'Trending', 'Viral', 'Exclusive', 'Update', 'Report', 'Review',
            'Tutorial', 'Guide', 'Tips', 'How To', 'List', 'Comparison'
        ]
        
        tags = []
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            tags.append(tag)

        # create articles
        self.stdout.write("Creating articles...")

        article_titles = [
            {
                "title": "Global Climate Summit Reaches Historic Agreement",
                "category": "Politics",
            },
            {
                "title": "New AI Model Breaks Performance Records",
                "category": "Technology",
            },
            {
                "title": "National Team Wins Championship After 20 Years",
                "category": "Sports",
            },
            {
                "title": "Blockbuster Movie Breaks Box Office Records",
                "category": "Entertainment",
            },
            {
                "title": "Tech Company Announces Revolutionary Product",
                "category": "Business",
            },
            {
                "title": "New Study Reveals Benefits of Mediterranean Diet",
                "category": "Health",
            },
            {
                "title": "Election Results Show Shift in Political Landscape",
                "category": "Politics",
            },
            {
                "title": "Quantum Computing Breakthrough Announced",
                "category": "Technology",
            },
            {"title": "Olympic Games Preparations Underway", "category": "Sports"},
            {"title": "Music Festival Lineup Announced", "category": "Entertainment"},
            {"title": "Stock Market Reaches All-Time High", "category": "Business"},
            {"title": "Breakthrough in Cancer Research", "category": "Health"},
        ]

        articles = []
        for i, article_data in enumerate(article_titles):
            category = Category.objects.get(name=article_data["category"])
            author = random.choice(journalists)
            article_tags = random.sample(tags, random.randint(2, 5))
            article, _ = Article.objects.get_or_create(
                title=article_data["title"],
                defaults={
                    "summary": f"This is a summary of the article: {article_data['title']}",
                    "content": f"This is the full content of the article: {article_data['title']}. "
                    * 20,
                    "author": author,
                    "category": category,
                    "status": "published",
                    "published_at": timezone.now()
                    - timezone.timedelta(days=random.randint(1, 30)),
                    "views_count": random.randint(100, 10000),
                    "is_featured": i < 3,
                },
            )

            # Add tags
            article.tags.set(article_tags)

            articles.append(article)

        # create comments
        self.stdout.write("Creating comments...")

        for article in articles:
            for _ in range(random.randint(0, 5)):
                user = random.choice(readers)
                comment = Comment.objects.create(
                    article=article,
                    user=user,
                    content=f'This is a comment on {article.title} by {user.username}.',
                )

                for _ in range(random.randint(0, 2)):
                    reply_user = random.choice(readers)
                    Comment.objects.create(
                        article=article,
                        user=reply_user,
                        parent=comment,
                        content=f'This is a reply to the comment by {user.username} on {article.title}.',
                    )

        # create likes and bookmarks
        self.stdout.write("Creating likes and bookmarks...")

        for article in articles:
            # random users like the article
            likers = random.sample(readers, random.randint(0, len(readers)))
            for user in likers:
                Like.objects.get_or_create(article=article, user=user)

            # random users bookmark the article
            bookmarkers = random.sample(readers, random.randint(0, len(readers)))
            for user in bookmarkers:
                Bookmark.objects.get_or_create(article=article, user=user)

        self.stdout.write(self.style.SUCCESS("Sample data created successfully"))
