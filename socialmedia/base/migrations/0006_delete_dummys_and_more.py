# Generated by Django 5.0.7 on 2024-08-02 09:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0005_dummys_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Dummys',
        ),
        migrations.RenameIndex(
            model_name='comment',
            new_name='Comments_id_cdc945_idx',
            old_name='Comment_id_91dcec_idx',
        ),
        migrations.RenameIndex(
            model_name='commentlike',
            new_name='Comment_Lik_id_68ec9f_idx',
            old_name='CommentLike_id_918326_idx',
        ),
        migrations.RenameIndex(
            model_name='post',
            new_name='Posts_id_6d8cd8_idx',
            old_name='Post_id_67e0e2_idx',
        ),
        migrations.RenameIndex(
            model_name='user',
            new_name='Users_email_838c41_idx',
            old_name='User_email_ffa2e0_idx',
        ),
        migrations.AlterModelTable(
            name='comment',
            table='Comments',
        ),
        migrations.AlterModelTable(
            name='commentlike',
            table='Comment_Likes',
        ),
        migrations.AlterModelTable(
            name='post',
            table='Posts',
        ),
        migrations.AlterModelTable(
            name='role',
            table='Roles',
        ),
        migrations.AlterModelTable(
            name='user',
            table='Users',
        ),
        migrations.AlterModelTable(
            name='userlog',
            table='User_Logs',
        ),
        migrations.AlterModelTable(
            name='userrole',
            table='UserRoles',
        ),
    ]