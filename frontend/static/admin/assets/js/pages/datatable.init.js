/** @format */

// /** @format */
// /** frontend/static/admin/assets/js/pages/datatable.min.js */

/** @format */
'use strict';

/** @format */
'use strict';

$(document).ready(function () {
    // ⚙️ Ngôn ngữ tiếng Việt mặc định
    $.extend(true, $.fn.dataTable.defaults, {
        language: {
            lengthMenu: 'Hiển thị _MENU_ mục',
            zeroRecords: 'Không tìm thấy kết quả',
            info: 'Hiển thị _START_ đến _END_ trong tổng _TOTAL_ mục',
            infoEmpty: 'Không có dữ liệu',
            infoFiltered: '(lọc từ _MAX_ mục)',
            search: 'Tìm kiếm:',
            paginate: {
                first: 'Đầu',
                last: 'Cuối',
                next: 'Sau',
                previous: 'Trước',
            },
        },
    });

    // ✅ Hàm tái sử dụng khởi tạo DataTable
    window.initDatatable = function (selector, options = {}) {
        const $table = $(selector);
        if (!$table.length || $.fn.dataTable.isDataTable($table)) return null;

        // Khởi tạo
        const table = $table.DataTable(options);
        return table;
    };

    // ✅ Xử lý checkbox chọn tất cả nếu có
    $('#select-all').on('click', function () {
        const checked = this.checked;
        $('.row-select').prop('checked', checked);
    });

    // ✅ Style lại select của length menu
    $("#datatable_length select[name*='datatable_length']")
        .addClass('form-select form-select-sm')
        .removeClass('custom-select custom-select-sm');
    $('.dataTables_length label').addClass('form-label');
});

// /** @format */
// 'use strict';

// $(document).ready(function () {
//     $.extend(true, $.fn.dataTable.defaults, {
//         language: {
//             lengthMenu: 'Hiển thị _MENU_ mục',
//             zeroRecords: 'Không tìm thấy kết quả',
//             info: 'Hiển thị _START_ đến _END_ trong tổng _TOTAL_ mục',
//             infoEmpty: 'Không có dữ liệu',
//             infoFiltered: '(lọc từ _MAX_ mục)',
//             search: 'Tìm kiếm:',
//             paginate: {
//                 first: 'Đầu',
//                 last: 'Cuối',
//                 next: 'Sau',
//                 previous: 'Trước',
//             },
//         },
//     });

//     // Bảng mặc định
//     $('#datatable').DataTable();

//     // Bảng có nút copy, print
//     const a = $('#datatable-buttons').DataTable({
//         lengthChange: false,
//         buttons: ['copy', 'print'],
//     });

//     // ✅ KHỞI TẠO CHỈ 1 LẦN VỚI ID 'scroll-horizontal-datatable'
//     const table = $('#scroll-horizontal-datatable').DataTable({
//         scrollX: true,
//         fixedColumns: {
//             leftColumns: 1, // Checkbox
//             rightColumns: 1, // Action
//         },
//         columnDefs: [
//             { orderable: false, targets: [0, 1, -1] }, // Checkbox, STT, Action không sắp xếp
//         ],
//         order: [[2, 'asc']], // Sắp xếp theo cột "Name"
//         lengthMenu: [5, 10, 20, 50, 100], // ✅ tuỳ chỉnh tại đây
//     });

//     // ✅ STT tự tăng
//     table
//         .on('order.dt search.dt draw.dt', function () {
//             table
//                 .column(1, { search: 'applied', order: 'applied' })
//                 .nodes()
//                 .each(function (cell, i) {
//                     cell.innerHTML = i + 1;
//                 });
//         })
//         .draw();

//     // Các bảng còn lại
//     $('#key-table').DataTable({ keys: true });
//     $('#responsive-datatable').DataTable();
//     $('#selection-datatable').DataTable({ select: { style: 'multi' } });
//     $('#alternative-page-datatable').DataTable({ pagingType: 'full_numbers' });
//     $('#scroll-vertical-datatable').DataTable({
//         scrollY: '350px',
//         scrollCollapse: true,
//         paging: false,
//     });
//     $('#complex-header-datatable').DataTable({
//         columnDefs: [{ visible: false, targets: -1 }],
//     });
//     $('#row-callback-datatable').DataTable({
//         createdRow: function (row, data) {
//             if (+data[5].replace(/[\$,]/g, '') > 150000) {
//                 $('td', row).eq(5).addClass('text-danger');
//             }
//         },
//     });
//     $('#state-saving-datatable').DataTable({ stateSave: true });
//     $('#fixed-columns-datatable').DataTable({
//         scrollY: 300,
//         scrollX: true,
//         scrollCollapse: true,
//         paging: false,
//         fixedColumns: true,
//     });
//     $('#fixed-header-datatable').DataTable({ responsive: true });

//     // Gắn nút vào header
//     a.buttons()
//         .container()
//         .appendTo('#datatable-buttons_wrapper .col-md-6:eq(0)');

//     // Style lại select của length
//     $("#datatable_length select[name*='datatable_length']").addClass(
//         'form-select form-select-sm'
//     );
//     $("#datatable_length select[name*='datatable_length']").removeClass(
//         'custom-select custom-select-sm'
//     );
//     $('.dataTables_length label').addClass('form-label');

//     // ✅ Chọn tất cả hàng
//     $('#select-all').on('click', function () {
//         var checked = this.checked;
//         $('.row-select').prop('checked', checked);
//     });
// });
