document.addEventListener('DOMContentLoaded', function() {
    const statusSelect = document.getElementById('status');
    const purchaseDataDiv = document.getElementById('purchaseData');

    function fetchPurchases(status) {
        fetch(`/get_purchases?status=${status}`)
            .then(response => response.json())
            .then(data => {
                displayPurchases(data, status);
            })
            .catch(error => {
                console.error('Error fetching purchases:', error);
                purchaseDataDiv.innerHTML = '<p class="no-data">Error loading purchases.</p>';
            });
    }

    function displayPurchases(purchases, status) {
        if (purchases.length === 0) {
            purchaseDataDiv.innerHTML = `<p class="no-data">No ${status} purchases found.</p>`;
            return;
        }

        let tableHtml = `
            <table>
                <thead>
                    <tr>
                        <th>Email</th>
                        <th>Username</th>
                        <th>Phone</th>
                        <th>Course Code</th>
                        <th>Title</th>
                        <th>Subtitle</th>
                        <th>Price</th>
                        <th>Original Price</th>
                        <th>Discount (%)</th>
                        <th>Final Price</th>
                        <th>Payment ID</th>
                        <th>Payment Mode</th>
                        <th>Payment Date</th>
                        <th>Purchase Code</th>
        `;
        if (status === 'Pending') {
            tableHtml += `<th>Action</th>`;
        }
        tableHtml += `
                    </tr>
                </thead>
                <tbody>
        `;

        purchases.forEach(purchase => {
            tableHtml += `
                <tr>
                    <td>${purchase.email}</td>
                    <td>${purchase.username || 'N/A'}</td>
                    <td>${purchase.phone || 'N/A'}</td>
                    <td>${purchase.course_code}</td>
                    <td>${purchase.title}</td>
                    <td>${purchase.subtitle || 'N/A'}</td>
                    <td>${purchase.price}</td>
                    <td>${purchase.original_price}</td>
                    <td>${purchase.discount_percent}</td>
                    <td>${purchase.final_price}</td>
                    <td>${purchase.payment_id}</td>
                    <td>${purchase.payment_mode || 'N/A'}</td>
                    <td>${new Date(purchase.payment_date).toLocaleString()}</td>
                    <td>${purchase.purchase_code}</td>
            `;
            if (status === 'Pending') {
                tableHtml += `<td><button class="delete-btn" data-id="${purchase.id}">Delete</button></td>`;
            }
            tableHtml += `
                </tr>
            `;
        });

        tableHtml += `
                </tbody>
            </table>
        `;
        purchaseDataDiv.innerHTML = tableHtml;

        if (status === 'Pending') {
            document.querySelectorAll('.delete-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const purchaseId = this.dataset.id;
                    if (confirm('Are you sure you want to delete this pending purchase? This action cannot be undone.')) {
                        deletePurchase(purchaseId);
                    }
                });
            });
        }
    }

    function deletePurchase(purchaseId) {
        fetch(`/delete_purchase/${purchaseId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Network response was not ok.');
        })
        .then(data => {
            alert(data.message);
            fetchPurchases(statusSelect.value); 
        })
        .catch(error => {
            console.error('Error deleting purchase:', error);
            alert('Error deleting purchase. Please try again.');
        });
    }

    
    statusSelect.addEventListener('change', function() {
        fetchPurchases(this.value);
    });

   
    fetchPurchases(statusSelect.value);
});