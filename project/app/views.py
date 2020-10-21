from rest_framework import serializers, viewsets
import datetime
from django.db.models import Q
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.generic.edit import FormView
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django_restful_admin import RestFulModelAdmin
from rest_framework.response import Response
from app.models import HoDan, Tinh
from app import models
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect
from app.forms import UploadFileForm, ConfirmationForm
from app.utils import temporary_files, validators


class BaseRestfulAdmin(RestFulModelAdmin):
    permission_classes = ()


class HoDanRestFulModelAdmin(BaseRestfulAdmin):
    def list(self, request):
        phone = request.GET.get("phone")
        tinh = request.GET.get("tinh")
        huyen = request.GET.get("huyen")
        xa = request.GET.get("xa")
        status = request.GET.get("status")
        fromTime = request.GET.get("from")
        toTime = request.GET.get("to")

        if phone or tinh or huyen or status or fromTime or toTime:
            filter = Q()
            if phone:
                filter = filter & Q(phone=phone)
            if tinh:
                filter = filter & Q(tinh=tinh)
            if huyen:
                filter = filter & Q(huyen=huyen)
            if xa:
                filter = filter & Q(xa=xa)
            if status:
                filter = filter & Q(status=status)
            if fromTime and toTime:
                start = datetime.datetime.strptime(
                    fromTime, "%Y-%m-%d-%H-%M-%S")
                end = datetime.datetime.strptime(toTime, "%Y-%m-%d-%H-%M-%S")
                filter = filter & Q(update_time__range=(start, end))

            queryset = HoDan.objects.filter(filter)
        else:
            # all if no filter
            queryset = HoDan.objects.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# /import_table/, /confirm_import_table/


MSG_INVALID_METHOD = 'Only accept GET and POST requests'


def handle_uploaded_file(f):
    path = temporary_files.get_temp_file_path(ensure_dir=True)
    with open(path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return temporary_files.path_to_name(path)


def import_table(request):
    if request.method == 'GET':
        form = UploadFileForm()
        return render(request, 'app/import_table_form.html', {'form': form})
    elif request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            name = handle_uploaded_file(request.FILES['file'])
            return HttpResponseRedirect('/confirm_import_table/{}/'.format(name))
        else:
            return render(request, 'app/import_table_form.html', {'form': form})
    else:
        return HttpResponseNotAllowed(MSG_INVALID_METHOD)


def confirm_import_table(request, uploaded_file_name):

    def dict_to_hodan(d):
        # TODO: fix magic number
        # ['Tên hộ dân', 'Tình trạng', 'Vị trí', 'Tỉnh', 'Xã', 'Huyện', 'Sdt', 'Cứu hộ', 'Thời gian cuối cùng cập nhật', 'Ghi chú']
        name = d["Tên hộ dân"]
        status = next(k for (k, v) in models.HODAN_STATUS if v ==
                      d["Tình trạng"]) if d["Tình trạng"] else 0
        location = d["Vị trí"]

        # By right, we should not create Tinh, Huyen, Xa at this step
        if d["Tỉnh"]:
            if models.Tinh.objects.filter(name=d["Tỉnh"]).exists():
                tinh = models.Tinh.objects.get(name=d["Tỉnh"])
            else:
                tinh = models.Tinh.objects.create(name=d["Tỉnh"])
                # tinh = None
        else:
            tinh = None

        if d["Huyện"] and tinh is not None:
            if models.Huyen.objects.filter(name=d["Huyện"], tinh=tinh).exists():
                huyen = models.Huyen.objects.get(name=d["Huyện"], tinh=tinh)
            else:
                huyen = models.Huyen.objects.create(name=d["Huyện"], tinh=tinh)
                # huyen = None
        else:
            huyen = None

        if d["Xã"] and huyen is not None:
            if models.Xa.objects.filter(name=d["Xã"], huyen=huyen).exists():
                xa = models.Xa.objects.get(name=d["Xã"], huyen=huyen)
            else:
                xa = models.Xa.objects.create(name=d["Xã"], huyen=huyen)
                # xa = None
        else:
            xa = None

        if d["Cứu hộ"]:
            if models.CuuHo.objects.filter(name=d["Cứu hộ"]).exists():
                cuuho = models.CuuHo.objects.get(name=d["Cứu hộ"])
            else:
                cuuho = None
        else:
            cuuho = None

        phone = d["Sdt"]
        update_time = datetime.datetime.strptime(
            d["Thời gian cuối cùng cập nhật"], "%d/%m/%Y %H:%M:%S") if d["Thời gian cuối cùng cập nhật"] else None
        # https://stackoverflow.com/questions/7499767/temporarily-disable-auto-now-auto-now-add
        # update_time is disregarded due to auto_now = True
        note = d["Ghi chú"]

        result = HoDan(
            name=name,
            status=status,
            location=location,
            tinh=tinh,
            huyen=huyen,
            xa=xa,
            thon=None,  # TODO: fix export file
            phone=phone,
            volunteer=None,  # TODO: fix export file
            cuuho=cuuho,
            update_time=update_time,
            note=note,
        )
        return result

    validation_result = validators.validate_import_table(uploaded_file_name)

    if request.method == 'GET' or validation_result["is_valid"] == False:
        form = ConfirmationForm()
        return render(request, 'app/confirm_import_table_form.html', {
            'form': form,
            'action': '/confirm_import_table/{}/'.format(uploaded_file_name)
        })
    elif request.method == 'POST':
        entries = validators.get_list_of_dict_from_data(uploaded_file_name)
        HoDan.objects.bulk_create(map(dict_to_hodan, entries))
        return HttpResponse("Success!")
    else:
        return HttpResponseNotAllowed(MSG_INVALID_METHOD)
