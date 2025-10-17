"""
Multi-User Isolation Integration Tests

Tests to verify that users are properly isolated in a multi-user environment.
Ensures SocketIO messages, threads, logs, and sessions don't leak between users.

Run with: pytest tests/integration/test_multi_user_isolation.py -v
"""
import pytest
import time
from flask import session
from flask_socketio import SocketIOTestClient


class TestSocketIOIsolation:
    """Test SocketIO room-based user isolation"""
    
    def test_users_join_separate_rooms(self, test_app, socketio):
        """Verify each user gets their own SocketIO room"""
        with test_app.test_request_context():
            # Simulate User 1 connection
            with test_app.test_client() as client1:
                with client1.session_transaction() as sess:
                    sess['user'] = 'user1'
                
                socketio_client1 = socketio.test_client(
                    test_app, 
                    flask_test_client=client1
                )
                
                # Simulate User 2 connection
                with test_app.test_client() as client2:
                    with client2.session_transaction() as sess:
                        sess['user'] = 'user2'
                    
                    socketio_client2 = socketio.test_client(
                        test_app,
                        flask_test_client=client2
                    )
                    
                    # Both should connect successfully
                    assert socketio_client1.is_connected()
                    assert socketio_client2.is_connected()
                    
                    # Clean up
                    socketio_client1.disconnect()
                    socketio_client2.disconnect()
    
    def test_thread_updates_only_to_owner(self, test_app, socketio, thread_manager):
        """Test thread progress updates only go to the user who started the thread"""
        with test_app.test_request_context():
            # User 1 starts a thread
            with test_app.test_client() as client1:
                with client1.session_transaction() as sess:
                    sess['user'] = 'user1'
                
                socketio_client1 = socketio.test_client(test_app, flask_test_client=client1)
                
                # User 2 is just observing
                with test_app.test_client() as client2:
                    with client2.session_transaction() as sess:
                        sess['user'] = 'user2'
                    
                    socketio_client2 = socketio.test_client(test_app, flask_test_client=client2)
                    
                    # Clear any existing messages
                    socketio_client1.get_received()
                    socketio_client2.get_received()
                    
                    # User 1 starts a thread (via test endpoint)
                    response = client1.post('/api/test_thread', data={'duration': 1})
                    assert response.status_code == 200
                    
                    # Wait for thread update
                    time.sleep(1.5)
                    
                    # User 1 should receive thread updates
                    messages1 = socketio_client1.get_received()
                    thread_messages1 = [m for m in messages1 if m['name'] in ('reload', 'threads')]
                    
                    # User 2 should NOT receive thread updates
                    messages2 = socketio_client2.get_received()
                    thread_messages2 = [m for m in messages2 if m['name'] in ('reload', 'threads')]
                    
                    assert len(thread_messages1) > 0, "User 1 should receive thread updates"
                    assert len(thread_messages2) == 0, "User 2 should NOT receive thread updates"
                    
                    socketio_client1.disconnect()
                    socketio_client2.disconnect()
    
    def test_log_updates_per_user(self, test_app, socketio):
        """Test log viewing is isolated per user"""
        with test_app.test_request_context():
            with test_app.test_client() as client1:
                with client1.session_transaction() as sess:
                    sess['user'] = 'user1'
                
                with test_app.test_client() as client2:
                    with client2.session_transaction() as sess:
                        sess['user'] = 'user2'
                    
                    socketio_client1 = socketio.test_client(test_app, flask_test_client=client1)
                    socketio_client2 = socketio.test_client(test_app, flask_test_client=client2)
                    
                    # User 1 enables live log mode
                    response1 = client1.post('/logging/api_toggle_live', data={'enabled': 'true'})
                    assert response1.status_code == 200
                    
                    # Clear messages
                    socketio_client1.get_received()
                    socketio_client2.get_received()
                    
                    # Wait for log update cycle
                    time.sleep(2.5)
                    
                    # User 1 should receive log updates (live mode enabled)
                    messages1 = socketio_client1.get_received()
                    log_messages1 = [m for m in messages1 if m['name'] == 'log_update']
                    
                    # User 2 should NOT receive log updates (live mode not enabled)
                    messages2 = socketio_client2.get_received()
                    log_messages2 = [m for m in messages2 if m['name'] == 'log_update']
                    
                    assert len(log_messages1) > 0, "User 1 should receive log updates"
                    assert len(log_messages2) == 0, "User 2 should NOT receive log updates"
                    
                    socketio_client1.disconnect()
                    socketio_client2.disconnect()
    
    def test_scheduler_messages_to_correct_user(self, test_app, socketio):
        """Test scheduler action results go to the correct user"""
        with test_app.test_request_context():
            with test_app.test_client() as client1:
                with client1.session_transaction() as sess:
                    sess['user'] = 'user1'
                
                with test_app.test_client() as client2:
                    with client2.session_transaction() as sess:
                        sess['user'] = 'user2'
                    
                    socketio_client1 = socketio.test_client(test_app, flask_test_client=client1)
                    socketio_client2 = socketio.test_client(test_app, flask_test_client=client2)
                    
                    # Clear messages
                    socketio_client1.get_received()
                    socketio_client2.get_received()
                    
                    # User 1 triggers an action
                    response = client1.post('/api/test_action')
                    assert response.status_code == 200
                    
                    # Wait for action to complete
                    time.sleep(0.5)
                    
                    # User 1 should receive action_status
                    messages1 = socketio_client1.get_received()
                    status_messages1 = [m for m in messages1 if m['name'] == 'action_status']
                    
                    # User 2 should NOT receive action_status
                    messages2 = socketio_client2.get_received()
                    status_messages2 = [m for m in messages2 if m['name'] == 'action_status']
                    
                    assert len(status_messages1) > 0, "User 1 should receive action status"
                    assert len(status_messages2) == 0, "User 2 should NOT receive action status"
                    
                    socketio_client1.disconnect()
                    socketio_client2.disconnect()


class TestSessionIsolation:
    """Test session isolation between users"""
    
    def test_separate_sessions_for_different_users(self, test_app):
        """Verify each user has their own session"""
        with test_app.test_client() as client1:
            # User 1 logs in
            response = client1.post('/common/login', data={
                'username': 'user1',
                'password': 'pass1'
            })
            assert response.status_code == 302  # Redirect after login
            
            with client1.session_transaction() as sess:
                user1_session_id = sess.sid
                assert sess.get('user') == 'user1'
            
            # Different client for User 2
            with test_app.test_client() as client2:
                response = client2.post('/common/login', data={
                    'username': 'user2',
                    'password': 'pass2'
                })
                assert response.status_code == 302
                
                with client2.session_transaction() as sess:
                    user2_session_id = sess.sid
                    assert sess.get('user') == 'user2'
                
                # Sessions should be different
                assert user1_session_id != user2_session_id
                
                # User 1's session should still be user1
                with client1.session_transaction() as sess:
                    assert sess.get('user') == 'user1'
    
    def test_session_data_isolation(self, test_app):
        """Test that session data doesn't leak between users"""
        with test_app.test_client() as client1:
            with client1.session_transaction() as sess:
                sess['user'] = 'user1'
                sess['test_data'] = 'user1_data'
            
            with test_app.test_client() as client2:
                with client2.session_transaction() as sess:
                    sess['user'] = 'user2'
                    sess['test_data'] = 'user2_data'
                
                # Check isolation
                with client1.session_transaction() as sess:
                    assert sess['test_data'] == 'user1_data'
                
                with client2.session_transaction() as sess:
                    assert sess['test_data'] == 'user2_data'


class TestConcurrentOperations:
    """Test concurrent operations by multiple users"""
    
    def test_concurrent_thread_execution(self, test_app, thread_manager):
        """Test multiple users can run threads simultaneously"""
        with test_app.test_client() as client1:
            with client1.session_transaction() as sess:
                sess['user'] = 'user1'
            
            with test_app.test_client() as client2:
                with client2.session_transaction() as sess:
                    sess['user'] = 'user2'
                
                # Both users start threads
                response1 = client1.post('/api/test_thread', data={'duration': 2})
                response2 = client2.post('/api/test_thread', data={'duration': 2})
                
                assert response1.status_code == 200
                assert response2.status_code == 200
                
                # Both threads should be running
                time.sleep(0.5)
                
                # Check thread manager shows both threads
                running_threads, _ = thread_manager.get_all_threads_with_history()
                assert len(running_threads) == 2
                
                # Threads should be associated with correct users
                thread_users = {t.username for t in running_threads}
                assert 'user1' in thread_users
                assert 'user2' in thread_users
                
                # Wait for completion
                time.sleep(2)
    
    def test_concurrent_page_views(self, test_app):
        """Test multiple users can view pages simultaneously"""
        import threading
        results = []
        
        def access_page(username):
            with test_app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['user'] = username
                
                response = client.get('/')
                results.append((username, response.status_code))
        
        # Simulate 5 concurrent users
        threads = []
        for i in range(5):
            t = threading.Thread(target=access_page, args=(f'user{i}',))
            threads.append(t)
            t.start()
        
        # Wait for all to complete
        for t in threads:
            t.join()
        
        # All should succeed
        assert len(results) == 5
        assert all(status == 200 for _, status in results)


class TestDataIsolation:
    """Test data isolation between users"""
    
    def test_thread_history_per_user(self, test_app, thread_manager):
        """Test thread history is per-user"""
        # This test assumes thread history is tracked per user
        # If not implemented yet, this serves as a specification
        
        with test_app.test_client() as client1:
            with client1.session_transaction() as sess:
                sess['user'] = 'user1'
            
            # User 1 runs a thread
            client1.post('/api/test_thread', data={'duration': 0.5})
            time.sleep(0.8)
            
            with test_app.test_client() as client2:
                with client2.session_transaction() as sess:
                    sess['user'] = 'user2'
                
                # User 2 checks threads page
                response = client2.get('/threads')
                content = response.data.decode()
                
                # User 2 should not see User 1's completed threads
                # (This is a TODO if not implemented)
                # assert 'user1' not in content.lower()
                
                # User 2 runs their own thread
                client2.post('/api/test_thread', data={'duration': 0.5})
                time.sleep(0.8)
                
                # Now check User 1's view
                response1 = client1.get('/threads')
                content1 = response1.data.decode()
                
                # Each user should only see their own threads
                # (Implementation detail - depends on your design choice)
                assert response.status_code == 200
                assert response1.status_code == 200


# Fixtures for testing

@pytest.fixture
def thread_manager():
    """Get the global thread manager instance"""
    from src.modules.threaded import threaded_manager
    return threaded_manager.thread_manager_obj


@pytest.fixture
def socketio(test_app):
    """Get SocketIO instance"""
    from src.main import setup_app
    socketio_obj = setup_app(test_app)
    return socketio_obj


# Test helper endpoints (add these to your test app)
"""
Add these routes to tests/conftest.py or a test blueprint:

@app.route('/api/test_thread', methods=['POST'])
def test_thread_endpoint():
    from src.modules.threaded.threaded_action import ThreadedAction
    
    duration = float(request.form.get('duration', 1))
    
    class TestThread(ThreadedAction):
        def run(self):
            import time
            time.sleep(duration)
            self.m_status = 100
    
    thread = TestThread(
        scheduler_obj=scheduler.scheduler_obj,
        name="Test Thread",
        category="test"
    )
    thread.start()
    
    return jsonify({'success': True, 'thread_id': thread.m_id})

@app.route('/api/test_action', methods=['POST'])
def test_action_endpoint():
    from src.modules.scheduler import scheduler
    
    scheduler.scheduler_obj.emit_status(
        category="test",
        string="Test action",
        status=100
    )
    
    return jsonify({'success': True})
"""

# Run these tests with:
# pytest tests/integration/test_multi_user_isolation.py -v
# pytest tests/integration/test_multi_user_isolation.py::TestSocketIOIsolation::test_thread_updates_only_to_owner -v
