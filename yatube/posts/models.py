from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Posts(models.Model):
    pub_date = models.DateTimeField(
        'Время публикации',
        auto_now_add=True,
        null=True
    )

    class Meta:
        abstract = True


class Group(models.Model):
    title = models.CharField('Название группы', max_length=200)
    slug = models.SlugField('Текст ссылки', unique=True)
    description = models.TextField('Описание группы')

    class Meta:
        verbose_name = 'Администрирование группы'
        verbose_name_plural = 'Администрирование групп'

    def __str__(self) -> str:
        return self.title


class Post(Posts):
    text = models.TextField('Текст поста', help_text='Введите текст поста')
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        verbose_name='Группа',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Администрирование поста'
        verbose_name_plural = 'Администрирование постов'
        ordering = ('-pub_date',)

    def __str__(self) -> str:
        return self.text[:15]


class Comment(Posts):
    post = models.ForeignKey(
        Post,
        verbose_name='Пост',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(
        'Текст комментария',
        help_text='Введите текст комментария'
    )

    class Meta:
        verbose_name = 'Администрирование комментария'
        verbose_name_plural = 'Администрирование комментариев'
        ordering = ('-pub_date',)

    def __str__(self) -> str:
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        verbose_name = 'Администрирование подписки'
        verbose_name_plural = 'Администрирование подписок'
        UniqueConstraint(fields=['user', 'author'], name='unique_following')

    def __str__(self) -> str:
        return self.text[:15]
