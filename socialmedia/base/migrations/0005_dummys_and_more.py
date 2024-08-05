# Generated by Django 5.0.7 on 2024-08-02 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_likes_counter'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dummys',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chars', models.CharField(max_length=20)),
            ],
            options={
                'db_table': 'Dummys',
            },
        ),
        migrations.RenameIndex(
            model_name='comment',
            new_name='Comment_id_91dcec_idx',
            old_name='base_commen_id_ecb2cd_idx',
        ),
        migrations.RenameIndex(
            model_name='commentlike',
            new_name='CommentLike_id_918326_idx',
            old_name='base_commen_id_fd1023_idx',
        ),
        migrations.RenameIndex(
            model_name='post',
            new_name='Post_id_67e0e2_idx',
            old_name='base_post_id_9fefe2_idx',
        ),
        migrations.RenameIndex(
            model_name='user',
            new_name='User_email_ffa2e0_idx',
            old_name='base_user_email_8a5bc6_idx',
        ),
        migrations.AlterModelTable(
            name='comment',
            table='Comment',
        ),
        migrations.AlterModelTable(
            name='commentlike',
            table='CommentLike',
        ),
        migrations.AlterModelTable(
            name='likes',
            table='Likes',
        ),
        migrations.AlterModelTable(
            name='post',
            table='Post',
        ),
        migrations.AlterModelTable(
            name='role',
            table='Role',
        ),
        migrations.AlterModelTable(
            name='user',
            table='User',
        ),
        migrations.AlterModelTable(
            name='userlog',
            table='UserLog',
        ),
        migrations.AlterModelTable(
            name='userrole',
            table='UserRole',
        ),
    ]
